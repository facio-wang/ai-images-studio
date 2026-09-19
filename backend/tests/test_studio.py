# 测试：鉴权 / 任务队列流转 / 资产 CRUD / 对话意图路由 / 模型中心
import base64
import io
import json
from urllib.parse import quote

import pytest
from PIL import Image

from tests.conftest import TOKEN, client as _c  # noqa: F401


def _png_bytes(w=64, h=64) -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), (255, 0, 0, 255)).save(buf, "PNG")
    return buf.getvalue()


# ---------- 鉴权 ----------

@pytest.mark.asyncio
async def test_root_no_auth(client):
    """/ 无需鉴权可访问"""
    r = await client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200


@pytest.mark.asyncio
async def test_api_requires_token(client):
    """无 token 访问受保护接口 → 401"""
    r = await client.get("/api/assets")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_api_with_token(client):
    """正确 token → 200 结构化响应"""
    r = await client.get("/api/assets", headers=TOKEN)
    assert r.status_code == 200
    assert r.json()["code"] == 200


# ---------- 对话意图路由 ----------

@pytest.mark.asyncio
async def test_chat_generate_intent(client, monkeypatch):
    """「生成一张…」路由到 generate 并创建任务"""
    # 屏蔽真实 ComfyUI：任务停在 queued 即可
    r = await client.post("/api/chat", headers=TOKEN, json={"message": "生成一张赛博朋克城市夜景"})
    body = r.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["intent"] == "generate"
    assert data["task_id"] is not None
    assert "生图任务" in data["content"]


@pytest.mark.asyncio
async def test_chat_matting_intent_no_asset(client):
    """「抠图」意图但无资产 → 引导提示，不建任务"""
    r = await client.post("/api/chat", headers=TOKEN, json={"message": "帮我抠图"})
    data = r.json()["data"]
    assert data["intent"] == "matting"
    assert data["task_id"] is None


@pytest.mark.asyncio
async def test_chat_unknown_intent(client):
    """无法识别意图 → 返回能力说明"""
    r = await client.post("/api/chat", headers=TOKEN, json={"message": "今天天气怎么样"})
    data = r.json()["data"]
    assert data["intent"] == "unknown"
    assert "生图" in data["content"]


@pytest.mark.asyncio
async def test_chat_session_persistence(client):
    """同一 session 消息历史可回查"""
    s = (await client.post("/api/chat", headers=TOKEN, json={"message": "查询任务进度"})).json()["data"]
    r = await client.get(f"/api/chat/messages?session_id={s['session_id']}", headers=TOKEN)
    msgs = r.json()["data"]
    assert len(msgs) >= 2
    assert msgs[0]["role"] == "user"


@pytest.mark.asyncio
async def test_chat_matting_with_asset(client):
    """上传资产后「把最近的图抠图」→ 创建 matting 任务"""
    up = await client.post("/api/assets/upload", headers=TOKEN, content=_png_bytes())
    asset_id = up.json()["data"]["id"]
    r = await client.post("/api/chat", headers=TOKEN, json={"message": "把最近的图抠图"})
    data = r.json()["data"]
    assert data["intent"] == "matting"
    assert data["task_id"] is not None
    return data


# ---------- 任务队列流转 ----------

@pytest.mark.asyncio
async def test_task_lifecycle_generate_failure(client, run_worker_once):
    """生图任务：ComfyUI 不可达 → 自动重试耗尽 → failed 且记录错误"""
    r = await client.post(
        "/api/generate", headers=TOKEN, json={"prompt": "测试", "count": 1, "steps": 1}
    )
    task = r.json()["data"]
    tid = task["id"]
    assert task["status"] == "queued"

    # 重试上限 2：执行 3 轮必到 failed
    for _ in range(3):
        await run_worker_once()
    r = await client.get(f"/api/tasks/{tid}", headers=TOKEN)
    task = r.json()["data"]
    assert task["status"] == "failed"
    assert task["retry_count"] == 2
    assert task["error"]


@pytest.mark.asyncio
async def test_task_matting_success(client, run_worker_once):
    """抠图任务：上传图 → 执行 → done + 透明 PNG 产物入库"""
    up = await client.post("/api/assets/upload", headers=TOKEN, content=_png_bytes())
    asset_id = up.json()["data"]["id"]
    r = await client.post("/api/matting", headers=TOKEN, json={"asset_id": asset_id, "model": "u2netp"})
    tid = r.json()["data"]["id"]

    await run_worker_once()
    task = (await client.get(f"/api/tasks/{tid}", headers=TOKEN)).json()["data"]
    assert task["status"] == "done", task.get("error")
    asset_ids = task["result_asset_ids"] if "result_asset_ids" in task else __import__("json").loads(task["result"])["asset_ids"]
    assert len(asset_ids) == 1
    out = (await client.get(f"/api/assets/{asset_ids[0]}", headers=TOKEN)).json()["data"]
    assert out["type"] == "matting"
    png = (await client.get(out["url"])).content
    img = Image.open(io.BytesIO(png))
    assert img.mode == "RGBA"


@pytest.mark.asyncio
async def test_task_retry_endpoint(client, run_worker_once):
    """失败任务可通过 /retry 重新排队"""
    r = await client.post("/api/generate", headers=TOKEN, json={"prompt": "x"})
    tid = r.json()["data"]["id"]
    for _ in range(3):
        await run_worker_once()
    r = await client.post(f"/api/tasks/{tid}/retry", headers=TOKEN)
    assert r.json()["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_generate_uses_default_checkpoint(client, run_worker_once, monkeypatch):
    """未指定底模时回退模型中心默认底模，任务执行成功（mock ComfyUI 调用）"""
    from app.services import generate

    # 添加默认底模
    await client.post(
        "/api/models", headers=TOKEN, json={"category": "checkpoint", "name": "test_default_sd"}
    )
    models = (await client.get("/api/models?category=checkpoint", headers=TOKEN)).json()["data"]
    target = next(m for m in models if m["name"] == "test_default_sd")
    await client.patch(f"/api/models/{target['id']}", headers=TOKEN, json={"is_default": True})

    captured = {}

    async def fake_txt2img(**kwargs):
        captured.update(kwargs)
        return [_png_bytes()]

    monkeypatch.setattr(generate, "txt2img", fake_txt2img)
    r = await client.post("/api/generate", headers=TOKEN, json={"prompt": "默认底模测试"})
    tid = r.json()["data"]["id"]
    await run_worker_once()
    task = (await client.get(f"/api/tasks/{tid}", headers=TOKEN)).json()["data"]
    assert task["status"] == "done", task.get("error")
    assert captured["checkpoint"] == "test_default_sd"


@pytest.mark.asyncio
async def test_generate_no_default_checkpoint_friendly_error(client, run_worker_once):
    """无默认底模时任务失败并给出友好错误提示"""
    # 确保无任何启用的 checkpoint 模型
    models = (await client.get("/api/models?category=checkpoint", headers=TOKEN)).json()["data"]
    for m in models:
        if m["enabled"]:
            await client.patch(f"/api/models/{m['id']}", headers=TOKEN, json={"enabled": False})

    r = await client.post("/api/generate", headers=TOKEN, json={"prompt": "无底模测试"})
    tid = r.json()["data"]["id"]
    # 自动重试耗尽后 failed
    for _ in range(3):
        await run_worker_once()
    task = (await client.get(f"/api/tasks/{tid}", headers=TOKEN)).json()["data"]
    assert task["status"] == "failed"
    assert "模型中心" in task["error"]

    # 手动重试入口可用：重置计数后可再次入队
    r = await client.post(f"/api/tasks/{tid}/retry", headers=TOKEN)
    assert r.json()["data"]["status"] == "queued"
    assert r.json()["data"]["retry_count"] == 0


# ---------- 资产 CRUD ----------

@pytest.mark.asyncio
async def test_asset_crud(client):
    """上传 → 查询 → 删除 全流程"""
    up = await client.post("/api/assets/upload", headers=TOKEN, content=_png_bytes())
    assert up.json()["code"] == 200
    asset = up.json()["data"]
    aid = asset["id"]
    assert asset["type"] == "upload"
    assert asset["url"].startswith("/files/")

    got = (await client.get(f"/api/assets/{aid}", headers=TOKEN)).json()["data"]
    assert got["id"] == aid

    # 文件可静态访问
    file_resp = await client.get(asset["url"])
    assert file_resp.status_code == 200

    # 列表分页
    listed = (await client.get("/api/assets?type=upload", headers=TOKEN)).json()["data"]
    assert listed["total"] >= 1

    deleted = await client.delete(f"/api/assets/{aid}", headers=TOKEN)
    assert deleted.json()["data"]["deleted"] is True
    gone = await client.get(f"/api/assets/{aid}", headers=TOKEN)
    assert gone.json()["code"] == 404


# ---------- 模型中心 ----------

@pytest.mark.asyncio
async def test_models_crud_and_default(client):
    """模型新增/启停/设默认/同分区唯一默认"""
    a = (await client.post("/api/models", headers=TOKEN, json={"category": "checkpoint", "name": "sd_xl_base"})).json()["data"]
    b = (await client.post("/api/models", headers=TOKEN, json={"category": "checkpoint", "name": "juggernautxl"})).json()["data"]

    # 设 b 为默认
    r = (await client.patch(f"/api/models/{b['id']}", headers=TOKEN, json={"is_default": True})).json()["data"]
    assert r["is_default"] == 1
    # 设 a 为默认后 b 被取消
    r = (await client.patch(f"/api/models/{a['id']}", headers=TOKEN, json={"is_default": True})).json()["data"]
    assert r["is_default"] == 1
    b2 = (await client.get(f"/api/models?category=checkpoint", headers=TOKEN)).json()["data"]
    defaults = [m for m in b2 if m["is_default"] == 1]
    assert len(defaults) == 1 and defaults[0]["id"] == a["id"]

    # 启停
    r = (await client.patch(f"/api/models/{a['id']}", headers=TOKEN, json={"enabled": False})).json()["data"]
    assert r["enabled"] == 0

    # 删除
    ok_del = (await client.delete(f"/api/models/{b['id']}", headers=TOKEN)).json()["data"]
    assert ok_del["deleted"] is True


@pytest.mark.asyncio
async def test_models_sync_comfyui_unreachable(client):
    """ComfyUI 不可达时同步返回失败但服务不崩"""
    r = await client.post("/api/models/sync-checkpoints", headers=TOKEN)
    body = r.json()
    assert body["code"] == 502
    assert "不可达" in body["msg"]


@pytest.mark.asyncio
async def test_translate_model_requires_base_url_and_model_id(client):
    """翻译模型 meta 缺 base_url/model_id → 400；齐全 → 成功入库"""
    r = await client.post(
        "/api/models", headers=TOKEN, json={"category": "translate", "name": "bad", "meta": {"api_key": "sk-x"}}
    )
    body = r.json()
    assert body["code"] == 400
    assert "base_url" in body["msg"] and "model_id" in body["msg"]

    ok_add = await client.post(
        "/api/models",
        headers=TOKEN,
        json={
            "category": "translate",
            "name": "deepseek",
            "meta": {"base_url": "https://api.deepseek.com/v1", "model_id": "deepseek-chat", "api_key": "sk-x"},
        },
    )
    assert ok_add.json()["code"] == 200
    meta = ok_add.json()["data"]["meta"]
    assert "base_url" in meta


# ---------- prompt 增强 ----------

@pytest.mark.asyncio
async def test_enhance_english_prompt_untouched(client):
    """纯英文 prompt 不做关键词映射，仅原样返回（不追加映射词）"""
    import aiosqlite

    from app.config import settings as app_settings
    from app.services import prompt_enhance

    async with aiosqlite.connect(app_settings.DB_PATH) as db:
        out = await prompt_enhance.enhance("a beautiful mountain landscape, oil painting", db)
    assert out == "a beautiful mountain landscape, oil painting"


@pytest.mark.asyncio
async def test_enhance_chinese_fallback_keyword_map(client, run_worker_once, monkeypatch):
    """无翻译模型时：中文 prompt 走内置关键词映射，workflow 收到的 text 含映射词"""
    from app.services import generate, task_service

    # 确保无启用的翻译模型
    models = (await client.get("/api/models?category=translate", headers=TOKEN)).json()["data"]
    for m in models:
        if m["enabled"]:
            await client.patch(f"/api/models/{m['id']}", headers=TOKEN, json={"enabled": False})

    # 默认底模
    await client.post(
        "/api/models", headers=TOKEN, json={"category": "checkpoint", "name": "ckpt_map_test"}
    )
    models = (await client.get("/api/models?category=checkpoint", headers=TOKEN)).json()["data"]
    target = next(m for m in models if m["name"] == "ckpt_map_test")
    await client.patch(f"/api/models/{target['id']}", headers=TOKEN, json={"is_default": True})

    captured = {}

    async def fake_txt2img(**kwargs):
        captured.update(kwargs)
        return [_png_bytes()]

    monkeypatch.setattr(generate, "txt2img", fake_txt2img)
    r = await client.post("/api/generate", headers=TOKEN, json={"prompt": "水墨插画风格的海报"})
    tid = r.json()["data"]["id"]
    await run_worker_once()
    task = (await client.get(f"/api/tasks/{tid}", headers=TOKEN)).json()["data"]
    assert task["status"] == "done", task.get("error")

    sent = captured["prompt"]
    assert "ink wash painting" in sent  # 水墨 → 映射词
    assert "illustration" in sent  # 插画 → 映射词
    assert "poster" in sent  # 海报 → 映射词
    # 映射降级路径：命中关键词后不再拼接中文正文，SDXL 只收英文
    assert "水墨" not in sent
    assert "插画" not in sent
    assert "海报" not in sent
    # 绘画类 prompt → negative 自动追加 photo 负面词
    assert "photo" in captured["negative"]
    # 任务结果记录实际发送的最终 prompt
    result = task["result"]
    if isinstance(result, str):
        result = json.loads(result)
    assert result["enhanced_prompt"] == sent


@pytest.mark.asyncio
async def test_enhance_chinese_no_keyword_hit_keeps_original(client):
    """中文 prompt 无任何映射命中且无翻译模型时：保留原文不崩溃（尽力而为）"""
    import aiosqlite

    from app.config import settings as app_settings
    from app.services import prompt_enhance

    async with aiosqlite.connect(app_settings.DB_PATH) as db:
        out = await prompt_enhance.enhance("一段毫无映射关键词的 arbitrary 文案", db)
    assert "一段毫无映射关键词的" in out
    assert "high quality" in out


@pytest.mark.asyncio
async def test_enhance_with_translate_model(client, run_worker_once, monkeypatch):
    """配置翻译模型时：走 OpenAI 兼容 /chat/completions 翻译（mock httpx）"""
    from app.services import generate, prompt_enhance, task_service

    await client.post(
        "/api/models",
        headers=TOKEN,
        json={
            "category": "translate",
            "name": "mock-translator",
            "meta": {"base_url": "https://mock.example/v1", "model_id": "mock-model", "api_key": "sk-t"},
        },
    )

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "cyberpunk city at night, neon lights"}}]}

    called = {}

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kwargs):
            called["url"] = url
            called["json"] = kwargs.get("json")
            return FakeResp()

    # 仅替换 prompt_enhance 使用的 httpx 客户端，避免影响测试自身的 ASGI client
    monkeypatch.setattr(prompt_enhance.httpx, "AsyncClient", FakeAsyncClient)

    await client.post(
        "/api/models", headers=TOKEN, json={"category": "checkpoint", "name": "ckpt_tr_test"}
    )
    models = (await client.get("/api/models?category=checkpoint", headers=TOKEN)).json()["data"]
    target = next(m for m in models if m["name"] == "ckpt_tr_test")
    await client.patch(f"/api/models/{target['id']}", headers=TOKEN, json={"is_default": True})

    async def fake_txt2img(**kwargs):
        return [_png_bytes()]

    monkeypatch.setattr(task_service.generate, "txt2img", fake_txt2img)
    r = await client.post("/api/generate", headers=TOKEN, json={"prompt": "赛博朋克城市的夜景"})
    tid = r.json()["data"]["id"]
    await run_worker_once()
    task = (await client.get(f"/api/tasks/{tid}", headers=TOKEN)).json()["data"]
    assert task["status"] == "done", task.get("error")
    # 翻译请求命中 OpenAI 兼容端点
    assert called["url"] == "https://mock.example/v1/chat/completions"
    assert called["json"]["model"] == "mock-model"


# ---------- MCP ----------

@pytest.mark.asyncio
async def test_mcp_requires_auth(client):
    """MCP 端点无 token → 401"""
    r = await client.post("/mcp", json={})
    assert r.status_code == 401


# ---------- 海报文字叠加 ----------

@pytest.mark.asyncio
async def test_render_texts_chinese_english():
    """中英文文字叠加：输出与原图不同、尺寸不变"""
    from app.services import text_render

    base = _png_bytes(512, 512)
    texts = [
        {"content": "限时买一得三", "x": "50%", "y": 100, "size": 48, "align": "center"},
        {"content": "VIP SALE", "x": 50, "y": 300, "size": 36, "color": "#FFD700", "stroke_width": 2},
    ]
    out = text_render.render_texts(base, texts)
    assert out != base
    img = Image.open(io.BytesIO(out))
    assert img.size == (512, 512)


@pytest.mark.asyncio
async def test_render_texts_percent_position():
    """x="50%" 正确换算为图宽一半的位置（渲染结果随百分比变化而不同）"""
    from app.services import text_render

    base = _png_bytes(512, 512)
    texts = [{"content": "测试", "x": "50%", "y": "50%", "size": 40}]
    out1 = text_render.render_texts(base, [dict(texts[0], x="10%")])
    out2 = text_render.render_texts(base, [dict(texts[0], x="80%")])
    assert out1 != out2
    # 百分比换算本身：50% of 512 == 256
    assert text_render._resolve_coord("50%", 512) == 256
    assert text_render._resolve_coord("50%", 1024) == 512


@pytest.mark.asyncio
async def test_texts_render_failure_fallback(client, run_worker_once, monkeypatch):
    """非法字体配置导致渲染失败：任务不 failed，返回原图 + warning"""
    from app.services import generate, text_render

    # 添加默认底模，确保生图本身能成功执行
    await client.post(
        "/api/models", headers=TOKEN, json={"category": "checkpoint", "name": "test_default_sd"}
    )
    models = (await client.get("/api/models?category=checkpoint", headers=TOKEN)).json()["data"]
    target = next(m for m in models if m["name"] == "test_default_sd")
    await client.patch(f"/api/models/{target['id']}", headers=TOKEN, json={"is_default": True})

    async def fake_txt2img(**kwargs):
        return [_png_bytes(64, 64)]

    monkeypatch.setattr(generate, "txt2img", fake_txt2img)

    def boom(image_bytes, texts):
        raise RuntimeError("字体损坏模拟")

    monkeypatch.setattr(text_render, "render_texts", boom)
    r = await client.post(
        "/api/generate",
        json={"prompt": "poster", "texts": [{"content": "文字", "font": "bad"}]},
        headers=TOKEN,
    )
    assert r.status_code == 200
    task_id = r.json()["data"]["id"]
    await run_worker_once()
    r2 = await client.get(f"/api/tasks/{task_id}", headers=TOKEN)
    body = r2.json()["data"]
    assert body["status"] == "done"
    result = json.loads(body["result"] or "{}")
    assert "warning" in result
    assert result["asset_ids"]


@pytest.mark.asyncio
async def test_poster_preview_endpoint(client):
    """/api/poster/preview：原始字节 + texts 查询参数 → PNG 预览"""
    r = await client.post(
        "/api/poster/preview?texts="
        + quote(json.dumps([{"content": "海报", "x": 10, "y": 10, "size": 32}], ensure_ascii=False)),
        content=_png_bytes(128, 128),
        headers={**TOKEN, "Content-Type": "application/octet-stream"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(r.content))
    assert img.size == (128, 128)
    # 非法 texts JSON → 400
    r2 = await client.post(
        "/api/poster/preview?texts=not-json", content=_png_bytes(), headers=TOKEN
    )
    # fail() 统一 HTTP 200 + 业务 code
    assert r2.json()["code"] == 400
