# API 路由层（瘦）：只做参数解析与响应组装，业务在 services
import base64

from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.deps import AuthContext, require_auth
from app.models import get_db
from app.response import CODE_NOT_FOUND, CODE_OK, fail, ok
from app.services import asset_service, chat_service, model_service, system_service, task_service

router = APIRouter(dependencies=[Depends(require_auth)])

# rembg 合法模型名（与 rembg sessions_class 对齐；birefnet 需带后缀，如 birefnet-general）
MATTING_MODELS = {
    "u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg",
    "bria-rmbg", "silueta", "isnet-general-use", "isnet-anime",
    "birefnet-general", "birefnet-general-lite", "birefnet-portrait",
    "birefnet-dis", "birefnet-hrsod", "birefnet-massive",
}

# 系统信息（无需鉴权，用于前端健康检查与系统状态面板）
meta_router = APIRouter()


def _image_ext(file: bytes) -> str | None:
    """按魔数识别图片格式，防止把 JSON 等非图片字节当成图片入库/入队"""
    if file.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if file.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if file.startswith(b"RIFF") and file[8:12] == b"WEBP":
        return "webp"
    if file[:3] == b"GIF":
        return "gif"
    return None


@meta_router.get("/")
async def root() -> dict:
    return {"code": CODE_OK, "msg": "ok", "data": {"name": "AI Images Studio", "version": "0.1.0"}}


# ---------- 系统状态（移植自 webUI-v1.0：生图服务状态 + 硬件资源占用） ----------

@meta_router.get("/api/system/status")
async def system_status() -> dict:
    """ComfyUI 连通性 + GPU 显存/设备 + 系统内存 + 队列，ComfyUI 不可达时降级不抛错"""
    return ok(await system_service.system_status())


# ---------- 任务中心 ----------

@router.get("/api/tasks")
async def list_tasks(status: str | None = None, limit: int = 100, db=Depends(get_db)):
    return ok(await task_service.list_tasks(db, status, limit))


@router.get("/api/tasks/{task_id}")
async def get_task(task_id: int, db=Depends(get_db)):
    task = await task_service.get_task(db, task_id)
    return ok(task) if task else fail(CODE_NOT_FOUND, f"任务不存在: {task_id}")


@router.post("/api/tasks/{task_id}/retry")
async def retry_task(task_id: int, db=Depends(get_db)):
    task = await task_service.retry_task(db, task_id)
    return ok(task) if task else fail(CODE_NOT_FOUND, f"任务不存在: {task_id}")


# ---------- 资产库 ----------

@router.get("/api/assets")
async def list_assets(
    type: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 40,
    db=Depends(get_db),
):
    return ok(await asset_service.list_assets(db, type, keyword, page, page_size))


@router.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int, db=Depends(get_db)):
    asset = await asset_service.get_asset(db, asset_id)
    return ok(asset) if asset else fail(CODE_NOT_FOUND, f"资产不存在: {asset_id}")


@router.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: int, db=Depends(get_db)):
    removed = await asset_service.delete_asset(db, asset_id)
    return ok({"deleted": removed}) if removed else fail(CODE_NOT_FOUND, f"资产不存在: {asset_id}")


@router.post("/api/assets/upload")
async def upload_asset(request: Request, label: str = "", db=Depends(get_db)):
    """上传图片入库（抠图源图/手工上传），body 为原始图片字节"""
    from app.utils import make_thumbnail, save_upload

    file = await request.body()
    if not file:
        return fail(400, "请求体不能为空")
    ext = _image_ext(file)
    if not ext:
        return fail(400, "请求体不是有效的图片文件（支持 PNG/JPG/WebP/GIF），请重新选择图片上传")
    filename = save_upload(file, ext)
    thumb = make_thumbnail(filename)
    asset = await asset_service.add_asset(
        db, "upload", filename, thumb, filename=filename, labels=label
    )
    return ok(asset)


# ---------- 生图 ----------

@router.post("/api/generate")
async def generate(payload: dict, db=Depends(get_db)):
    """提交生图任务：prompt 必填，其余参数可选。提交前预检 ComfyUI，未启动立即明确报错"""
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return fail(400, "prompt 不能为空")
    # 预检：生图服务未启动时立即告知用户，而不是任务入队后静默重试耗尽
    if not await system_service.comfy_ping():
        return fail(
            503,
            f"生图服务（ComfyUI {settings.COMFYUI_URL}）未启动或不可达，请先在 Win11 宿主机启动 ComfyUI 后重试",
        )
    params = {
        "prompt": prompt,
        "checkpoint": payload.get("checkpoint"),
        "width": payload.get("width", 1024),
        "height": payload.get("height", 1024),
        "steps": payload.get("steps", 20),
        "cfg": payload.get("cfg", 7.0),
        "seed": payload.get("seed", -1),
        "count": payload.get("count", 1),
        # 海报文字叠加配置直接透传（不做严格校验，渲染层容错）
        "texts": payload.get("texts"),
    }
    task = await task_service.create_task(db, "generate", params)
    return ok(task)


# ---------- 抠图 ----------

@router.post("/api/matting")
async def matting(payload: dict, db=Depends(get_db)):
    """提交抠图任务：asset_id 或 image_base64 二选一"""
    if not payload.get("asset_id") and not payload.get("image_base64"):
        return fail(400, "需要 asset_id 或 image_base64")
    model = payload.get("model")
    if model and model not in MATTING_MODELS:
        return fail(400, f"不支持的抠图模型: {model}，可选: {', '.join(sorted(MATTING_MODELS))}")
    task = await task_service.create_task(db, "matting", payload)
    return ok(task)


@router.post("/api/matting/upload")
async def matting_upload(request: Request, model: str = "bria-rmbg", db=Depends(get_db)):
    """直接上传图片并提交抠图任务，body 为原始图片字节"""
    if model not in MATTING_MODELS:
        return fail(400, f"不支持的抠图模型: {model}，可选: {', '.join(sorted(MATTING_MODELS))}")
    file = await request.body()
    if not file:
        return fail(400, "请求体不能为空")
    if not _image_ext(file):
        return fail(400, "上传内容不是有效的图片文件（支持 PNG/JPG/WebP/GIF），请重新选择图片后提交")
    task = await task_service.create_task(
        db, "matting", {"image_base64": base64.b64encode(file).decode(), "model": model}
    )
    return ok(task)


# ---------- 海报文字叠加 ----------

@router.post("/api/poster/preview")
async def poster_preview(request: Request):
    """海报文字预览：multipart 文件或原始字节图片 + texts 配置 → 返回渲染后 PNG 字节

    用法一：multipart 表单（image 文件 + texts JSON 字符串）
    用法二：body 为图片原始字节，texts 经查询参数 texts（JSON 字符串）传入
    """
    import json as _json

    from fastapi import Response

    from app.services import text_render

    # 优先 multipart 表单
    image_bytes = b""
    texts_raw = request.query_params.get("texts", "")
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("image")
        if upload is not None:
            image_bytes = await upload.read()
        texts_raw = form.get("texts") or texts_raw or ""
    else:
        image_bytes = await request.body()
    if not image_bytes:
        return fail(400, "请求体不能为空（需上传图片）")
    try:
        texts = _json.loads(texts_raw) if texts_raw else []
    except _json.JSONDecodeError:
        return fail(400, "texts 不是合法 JSON")
    try:
        out = text_render.render_texts(image_bytes, texts)
    except RuntimeError as exc:  # 字体缺失等明确错误
        return fail(500, str(exc))
    return Response(content=out, media_type="image/png")


# ---------- 模型中心 ----------

@router.get("/api/models")
async def list_models(category: str | None = None, db=Depends(get_db)):
    return ok(await model_service.list_models(db, category))


@router.post("/api/models")
async def add_model(payload: dict, db=Depends(get_db)):
    category = payload.get("category")
    name = (payload.get("name") or "").strip()
    if category not in model_service.CATEGORIES or not name:
        return fail(400, "category 或 name 非法")
    meta = payload.get("meta") or {}
    if not isinstance(meta, dict):
        return fail(400, "meta 必须是 JSON 对象")
    # 翻译模型依赖 meta 里的 base_url/model_id 调用 OpenAI 兼容接口，缺一不可
    if category == "translate":
        missing = [k for k in ("base_url", "model_id") if not str(meta.get(k) or "").strip()]
        if missing:
            return fail(400, f"翻译模型需要提供配置字段: {', '.join(missing)}")
    return ok(await model_service.add_model(db, category, name, meta))


@router.patch("/api/models/{model_id}")
async def update_model(model_id: int, payload: dict, db=Depends(get_db)):
    model = await model_service.update_model(db, model_id, payload)
    return ok(model) if model else fail(CODE_NOT_FOUND, f"模型不存在: {model_id}")


@router.delete("/api/models/{model_id}")
async def delete_model(model_id: int, db=Depends(get_db)):
    removed = await model_service.delete_model(db, model_id)
    return ok({"deleted": removed}) if removed else fail(CODE_NOT_FOUND, f"模型不存在: {model_id}")


@router.post("/api/models/sync-checkpoints")
async def sync_checkpoints(db=Depends(get_db)):
    """从 ComfyUI 同步底模列表（不可达时返回 failed 但不影响服务）"""
    try:
        return ok(await model_service.sync_checkpoints_from_comfyui(db))
    except Exception as exc:
        return fail(502, f"ComfyUI 不可达: {exc}")


# ---------- 对话工作台 ----------

@router.get("/api/chat/sessions")
async def list_sessions(db=Depends(get_db)):
    return ok(await chat_service.list_sessions(db))


@router.get("/api/chat/messages")
async def get_messages(session_id: int, db=Depends(get_db)):
    return ok(await chat_service.get_messages(db, session_id))


@router.post("/api/chat")
async def chat(payload: dict, db=Depends(get_db)):
    """发消息：{message, session_id?} → AI 回复 + 触发任务/产物"""
    message = (payload.get("message") or "").strip()
    if not message:
        return fail(400, "消息不能为空")
    # 生图/抠图意图前先预检 ComfyUI：未启动时直接告知，不让对话"运行一会儿静默停止"
    if chat_service.looks_like_image_intent(message) and not await system_service.comfy_ping():
        return ok(
            {
                "session_id": payload.get("session_id"),
                "message_id": 0,
                "content": (
                    f"⚠️ 生图服务（ComfyUI {settings.COMFYUI_URL}）当前未启动，无法执行生图/抠图。"
                    "请先在 Win11 宿主机启动 ComfyUI（运行 comfyui 启动脚本，端口 8188），"
                    "启动成功后重新发送本条消息即可。"
                ),
                "intent": "service_down",
                "task_id": None,
                "asset_ids": [],
            }
        )
    result = await chat_service.send_message(db, payload.get("session_id"), message)
    return ok(result)


@router.get("/api/chat/quick-commands")
async def quick_commands():
    return ok(chat_service.quick_commands())
