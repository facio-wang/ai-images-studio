# LoRA 训练 API（瘦路由层）：
# - 数据集管理：文件系统真源（docker 卷 data/lora_datasets），后端直接落盘
# - 训练控制：代理宿主机助手（COMFYUI_START_AGENT）的 /train/* 端点，训练跑在宿主机 GPU
# 代理失败一律降级为明确中文 message（fail 502），永不抛 500
import logging

import httpx
from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.deps import require_auth
from app.response import fail, ok
from app.services import lora_service

logger = logging.getLogger("studio.lora")

router = APIRouter(dependencies=[Depends(require_auth)])

# 助手是本机/内网常驻服务，10s 足够；trust_env=False 避免容器代理变量劫持 localhost 流量
_AGENT_TIMEOUT = 10.0


async def _agent_call(method: str, path: str, *, params=None, json_body=None):
    """调用宿主机助手端点。成功返回 (payload_dict, None)，失败返回 (None, 中文错误说明)。"""
    agent = settings.COMFYUI_START_AGENT.strip()
    if not agent:
        return None, (
            "尚未配置 COMFYUI_START_AGENT：LoRA 训练在宿主机 GPU 上执行，"
            "依赖常驻助手（仓库 scripts/host/comfyui_launcher.py），请在 .env 配置后使用"
        )
    try:
        async with httpx.AsyncClient(timeout=_AGENT_TIMEOUT, trust_env=False) as client:
            r = await client.request(
                method, f"{agent.rstrip('/')}{path}", params=params, json=json_body
            )
    except Exception as exc:
        logger.warning("宿主机启动助手不可达: %s", exc)
        return None, (
            f"无法连接宿主机启动助手（{agent}）：请确认助手已常驻运行"
            "（仓库 scripts/host/install-autostart.bat 注册开机自启）"
        )
    if r.status_code != 200:
        try:
            msg = r.json().get("message", "")
        except Exception:
            msg = r.text[:200]
        return None, f"宿主机助手返回 {r.status_code}：{msg}"
    try:
        return r.json(), None
    except Exception:
        return None, "宿主机助手返回了非 JSON 响应"


# ---------- 数据集管理（文件系统真源） ----------


@router.get("/api/lora/datasets")
async def list_datasets():
    return ok(lora_service.list_datasets())


@router.post("/api/lora/datasets")
async def create_dataset(payload: dict):
    try:
        created = lora_service.create_dataset(payload.get("name") or "")
    except ValueError as exc:
        return fail(400, str(exc))
    return ok(created)


@router.delete("/api/lora/datasets/{name}")
async def delete_dataset(name: str):
    try:
        removed = lora_service.delete_dataset(name)
    except ValueError as exc:
        return fail(400, str(exc))
    except FileNotFoundError as exc:
        return fail(404, str(exc))
    return ok({"deleted": removed})


def _parse_multipart_files(body: bytes, content_type: str) -> list[tuple[str, bytes]]:
    """极简 multipart/form-data 解析（纯标准库，二进制安全）。

    运行镜像未安装 python-multipart，FastAPI 的 File()/UploadFile 会在导入期硬性报错，
    故按浏览器 FormData 生成的报文结构手工切分；只取字段名为 files 的文件项。
    RFC 2046：分隔符前的 CRLF 属于边界，不属于 payload，切分时剥掉。
    """
    boundary = ""
    for item in content_type.split(";"):
        item = item.strip()
        if item.lower().startswith("boundary="):
            boundary = item.split("=", 1)[1].strip().strip('"')
    if not boundary:
        return []
    delim = b"--" + boundary.encode("latin-1")
    files: list[tuple[str, bytes]] = []
    for section in body.split(delim):
        if not section or section.startswith(b"--"):  # 前导空段 / 收尾 "--"
            continue
        head, sep, payload = section.partition(b"\r\n\r\n")
        if not sep:
            continue
        if payload.endswith(b"\r\n"):
            payload = payload[:-2]
        headers = head.decode("latin-1", "replace")
        if 'name="files"' not in headers:
            continue
        marker = 'filename="'
        idx = headers.find(marker)
        filename = headers[idx + len(marker):].split('"', 1)[0] if idx >= 0 else ""
        if filename:
            files.append((filename, payload))
    return files


@router.post("/api/lora/datasets/{name}/upload")
async def upload_images(name: str, request: Request):
    """多图上传入数据集（multipart 字段 files，可重复）：逐个校验扩展名/大小（<15MB）"""
    try:
        lora_service.dataset_dir(name)
    except ValueError as exc:
        return fail(400, str(exc))
    except FileNotFoundError as exc:
        return fail(404, str(exc))

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        return fail(400, "请使用 multipart/form-data 上传（字段名 files）")
    body = await request.body()
    picked = _parse_multipart_files(body, content_type)

    saved = 0
    for filename, data in picked:
        try:
            lora_service.save_image(name, filename, data)
            saved += 1
        except ValueError as exc:
            logger.warning("跳过不合规样本 %s: %s", filename, exc)
        except Exception as exc:
            logger.warning("保存样本失败 %s: %s", filename, exc)
    if saved == 0:
        return fail(400, "没有可保存的图片：请确认文件为 png/jpg/jpeg/webp 且单张不超过 15MB")
    return ok({"saved": saved})


@router.delete("/api/lora/datasets/{name}/images/{filename}")
async def delete_image(name: str, filename: str):
    try:
        removed = lora_service.delete_image(name, filename)
    except ValueError as exc:
        return fail(400, str(exc))
    except FileNotFoundError as exc:
        return fail(404, str(exc))
    return ok({"deleted": removed}) if removed else fail(404, f"图片不存在: {filename}")


# ---------- 训练控制（代理宿主机助手） ----------


@router.get("/api/lora/env")
async def train_env():
    """训练环境检测：代理助手 GET /train/env，未就绪时前端展示 items 明细"""
    payload, error = await _agent_call("GET", "/train/env")
    if error:
        return fail(502, error)
    return ok(payload)


@router.post("/api/lora/train")
async def start_train(payload: dict):
    """开始训练：代理助手 POST /train/start（token 由后端附加，前端不接触 token）"""
    dataset = (payload.get("dataset") or "").strip()
    trigger = (payload.get("trigger") or "").strip()
    try:
        lora_service.validate_name(dataset, label="数据集名")
        lora_service.validate_name(trigger, label="触发词")
    except ValueError as exc:
        return fail(400, str(exc))
    result, error = await _agent_call(
        "POST", "/train/start", json_body={"token": settings.STUDIO_TOKEN, "dataset": dataset, "trigger": trigger}
    )
    if error:
        return fail(502, error)
    return ok(result)


@router.post("/api/lora/train/stop")
async def stop_train(payload: dict):
    """停止训练：代理助手 POST /train/stop（按 PID 记录终止）"""
    dataset = (payload.get("dataset") or "").strip()
    try:
        lora_service.validate_name(dataset, label="数据集名")
    except ValueError as exc:
        return fail(400, str(exc))
    result, error = await _agent_call(
        "POST", "/train/stop", json_body={"token": settings.STUDIO_TOKEN, "dataset": dataset}
    )
    if error:
        return fail(502, error)
    return ok(result)


@router.get("/api/lora/train/status")
async def train_status(dataset: str = ""):
    """训练状态：代理助手 GET /train/status（running + 日志尾部 60 行），透传 JSON"""
    try:
        lora_service.validate_name(dataset, label="数据集名")
    except ValueError as exc:
        return fail(400, str(exc))
    result, error = await _agent_call(
        "GET", "/train/status", params={"dataset": dataset, "token": settings.STUDIO_TOKEN}
    )
    if error:
        return fail(502, error)
    return ok(result)
