# 任务服务：任务队列核心（SQLite tasks 表 + asyncio 后台 worker）
import asyncio
import json
import logging
import traceback
from datetime import datetime

import aiosqlite

from app.config import settings
from app.models import fetch_all, fetch_one
from app.services import generate, matting, model_service, prompt_enhance, text_render
from app.utils import make_thumbnail, new_name, save_upload

logger = logging.getLogger("studio.worker")

# 已注册的任务处理器：type → async fn(params, db) -> dict(result)
_handlers: dict[str, object] = {}


def register_handlers() -> None:
    """注册 P1 任务类型（generate/matting）"""
    _handlers["generate"] = _run_generate
    _handlers["matting"] = _run_matting


async def create_task(db: aiosqlite.Connection, task_type: str, params: dict) -> dict:
    """创建任务（queued 状态）"""
    cur = await db.execute(
        "INSERT INTO tasks(type, params, max_retry) VALUES(?,?,?)",
        (task_type, json.dumps(params, ensure_ascii=False), settings.TASK_MAX_RETRY),
    )
    task_id = cur.lastrowid
    return await get_task(db, task_id)


async def get_task(db: aiosqlite.Connection, task_id: int) -> dict | None:
    return await fetch_one(db, "SELECT * FROM tasks WHERE id=?", (task_id,))


async def list_tasks(db: aiosqlite.Connection, status: str | None = None, limit: int = 100) -> list[dict]:
    if status:
        return await fetch_all(
            db, "SELECT * FROM tasks WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit)
        )
    return await fetch_all(db, "SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,))


async def retry_task(db: aiosqlite.Connection, task_id: int) -> dict | None:
    """手动重试：failed → queued，重置错误与重试计数（允许失败任务无限次手动重试）"""
    task = await get_task(db, task_id)
    if not task:
        return None
    await db.execute(
        "UPDATE tasks SET status='queued', error=NULL, retry_count=0,"
        " updated_at=datetime('now','localtime') WHERE id=?",
        (task_id,),
    )
    return await get_task(db, task_id)


# ---------- 任务处理器 ----------

async def _run_generate(params: dict, db: aiosqlite.Connection, task_id: int | None = None) -> dict:
    """生图：调 ComfyUI → 产物入库 assets"""
    checkpoint = params.get("checkpoint")
    model_row = None
    if not checkpoint:
        # 未指定底模时回退到模型中心默认底模（checkpoint 分区）
        default_model = await model_service.get_default_model(db, "checkpoint")
        if not default_model:
            raise ValueError(
                "尚未配置底模：请到「模型中心」同步 ComfyUI 底模并设为默认"
            )
        checkpoint = default_model["name"]
        model_row = default_model
    else:
        model_row = await fetch_one(
            db, "SELECT * FROM models WHERE category='checkpoint' AND name=?", (checkpoint,)
        )
    # 按模型中心 meta 推断工作流类型（z_image 走 GGUF+Qwen3 工作流，原生支持中文）
    model_type = model_service.infer_model_type(checkpoint, model_row["meta"] if model_row else None)
    is_z_image = model_type == "z_image"
    # 生图可挂模型中心启用的 LoRA（meta.strength 可调强度，默认 1.0）
    loras = []
    for row in await model_service.list_models(db, "lora"):
        if not row["enabled"]:
            continue
        meta = row["meta"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (TypeError, ValueError):
                meta = {}
        strength = 1.0
        if isinstance(meta, dict):
            try:
                strength = float(meta.get("strength", 1.0))
            except (TypeError, ValueError):
                strength = 1.0
        loras.append({"name": row["name"], "strength": strength})
    # 中文 prompt 处理：Z-Image 原生中文直出；其余底模发送前增强为"中文原意+英文关键词"
    raw_prompt = params.get("prompt", "")
    if is_z_image:
        # Z-Image 原生中文：指令式需求（"生成一张XX图"）先改写为描述性提示词，已是描述则原样直出
        enhanced_prompt = await prompt_enhance.rewrite_native(db, raw_prompt)
        negative = params.get("negative", generate.DEFAULT_NEGATIVE)
    else:
        enhanced_prompt = await prompt_enhance.enhance(raw_prompt, db)
        negative = params.get("negative", generate.DEFAULT_NEGATIVE)
        negative = prompt_enhance.adjust_negative(enhanced_prompt, negative)
    logger.info(
        "生图 prompt (model_type=%s, loras=%d): %r -> %r, negative=%r",
        model_type, len(loras), raw_prompt[:50], enhanced_prompt[:120], negative[:80],
    )
    images = await generate.txt2img(
        prompt=enhanced_prompt,
        checkpoint=checkpoint,
        width=int(params.get("width", 1024)),
        height=int(params.get("height", 1024)),
        steps=int(params.get("steps", 20)),
        cfg=float(params.get("cfg", 7.0)),
        seed=int(params.get("seed", -1)),
        count=int(params.get("count", 1)),
        negative=negative,
        model_type=model_type,
        loras=loras,
    )
    # 海报文字叠加：params.texts 非空时在产物上渲染真实可读文字
    texts = params.get("texts") or []
    warning = None
    if texts and not isinstance(texts, list):
        texts = []
    asset_ids = []
    for img in images:
        if texts:
            try:
                # 渲染失败降级：返回原图 + warning，不标 failed（生成本身已成功）
                img = text_render.render_texts(img, texts)
            except Exception as exc:
                logger.warning("文字渲染失败，降级返回原图: %s", exc)
                warning = f"文字渲染失败，已返回原图: {exc}"
        filename = save_upload(img, "png")
        asset_ids.append(await _insert_asset(db, "generate", filename, params.get("prompt", ""), task_id))
    result = {"asset_ids": asset_ids, "enhanced_prompt": enhanced_prompt}
    if warning:
        result["warning"] = warning
    return result


async def _run_matting(params: dict, db: aiosqlite.Connection, task_id: int | None = None) -> dict:
    """抠图：源图（asset_id 或上传 base64）→ 透明 PNG 入库"""
    image_bytes = await _resolve_source_image(db, params)
    model = params.get("model")
    if not model:
        # 未指定抠图模型时回退到模型中心默认（matting 分区），取不到则用内置默认
        default_model = await model_service.get_default_model(db, "matting")
        if default_model:
            model = default_model["name"]
    out = await matting.remove_background(image_bytes, model)
    filename = save_upload(out, "png")
    asset_id = await _insert_asset(db, "matting", filename, params.get("label", ""), task_id)
    return {"asset_ids": [asset_id]}


async def _resolve_source_image(db: aiosqlite.Connection, params: dict) -> bytes:
    """任务源图解析：asset_id 引用 或 base64 内联"""
    import base64

    if params.get("asset_id"):
        row = await fetch_one(db, "SELECT file_path FROM assets WHERE id=?", (params["asset_id"],))
        if not row:
            raise ValueError(f"资产不存在: {params['asset_id']}")
        return (settings.ASSETS_DIR / row["file_path"]).read_bytes()
    if params.get("image_base64"):
        return base64.b64decode(params["image_base64"])
    raise ValueError("缺少源图（asset_id 或 image_base64）")


async def _insert_asset(db: aiosqlite.Connection, asset_type: str, filename: str, label: str, task_id: int | None = None) -> int:
    thumb = make_thumbnail(filename)
    cur = await db.execute(
        "INSERT INTO assets(type, file_path, thumb_path, labels, source_task_id) VALUES(?,?,?,?,?)",
        (asset_type, filename, thumb, label[:100], task_id),
    )
    return cur.lastrowid


# ---------- 后台 worker ----------

async def _claim_next_task() -> tuple[aiosqlite.Connection, dict] | None:
    """取出一个 queued 任务并置为 running，返回 (连接, 任务行)"""
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        row = await (
            await db.execute(
                "SELECT * FROM tasks WHERE status='queued' ORDER BY id ASC LIMIT 1"
            )
        ).fetchone()
        if row is None:
            await db.close()
            return None
        await db.execute(
            "UPDATE tasks SET status='running', updated_at=datetime('now','localtime') WHERE id=?",
            (row["id"],),
        )
        await db.commit()
        task = await fetch_one(db, "SELECT * FROM tasks WHERE id=?", (row["id"],))
        return db, task
    except Exception:
        await db.close()
        raise


def _claim_task_row(db: aiosqlite.Connection) -> dict | None:
    """（同步辅助）从已抢占连接中取 running 任务行 —— 仅供测试驱动使用"""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        fetch_one(db, "SELECT * FROM tasks WHERE status='running' ORDER BY id DESC LIMIT 1")
    )


async def _execute_claimed(db: aiosqlite.Connection, task: dict) -> None:
    """执行已抢占任务并写回结果/失败状态（含重试计数）"""
    task_id = task["id"]
    try:
        params = json.loads(task["params"] or "{}")
        handler = _handlers.get(task["type"])
        if handler is None:
            raise ValueError(f"未知任务类型: {task['type']}")
        result = await handler(params, db, task_id=task["id"])
        result = result if isinstance(result, dict) else {}
        # 详情弹窗展示用：生图任务把实际生效的底模/工作流类型/增强后提示词一并写进 result
        if task["type"] == "generate":
            checkpoint = params.get("checkpoint")
            if not checkpoint:
                default_model = await model_service.get_default_model(db, "checkpoint")
                checkpoint = default_model["name"] if default_model else None
            result["model"] = checkpoint
            row = (
                await fetch_one(db, "SELECT meta FROM models WHERE category='checkpoint' AND name=?", (checkpoint,))
                if checkpoint
                else None
            )
            meta = json.loads(row["meta"]) if row and isinstance(row["meta"], str) else (row["meta"] if row else None)
            result["model_type"] = model_service.infer_model_type(checkpoint, meta)
            result["params_snapshot"] = {
                k: params.get(k)
                for k in ("prompt", "width", "height", "steps", "cfg", "seed", "count", "negative")
                if params.get(k) is not None
            }
        await db.execute(
            "UPDATE tasks SET status='done', result=?, finished_at=datetime('now','localtime'),"
            " updated_at=datetime('now','localtime') WHERE id=?",
            (json.dumps(result, ensure_ascii=False), task_id),
        )
        await db.commit()
        logger.info("任务完成 #%s type=%s", task_id, task["type"])
    except Exception as exc:
        await db.rollback()
        # 重试语义：max_retry=2 表示额外重试 2 次（共执行 3 次），耗尽后 failed
        retry_count = min(task["retry_count"] + 1, task["max_retry"])
        exhausted = task["retry_count"] + 1 > task["max_retry"]
        status = "queued" if not exhausted else "failed"
        err = f"{exc}\n{traceback.format_exc(limit=3)}"
        logger.warning("任务 #%s 失败(重试%s/%s): %s", task_id, retry_count, task["max_retry"], exc)
        await db.execute(
            "UPDATE tasks SET status=?, error=?, retry_count=?, finished_at=?,"
            " updated_at=datetime('now','localtime') WHERE id=?",
            (
                status,
                err,
                retry_count,
                datetime.now().isoformat(timespec="seconds") if status == "failed" else None,
                task_id,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def worker_loop() -> None:
    """后台 worker 主循环：轮询 queued 任务逐个执行"""
    register_handlers()
    logger.info("任务 worker 启动 (poll=%.1fs)", settings.WORKER_POLL_INTERVAL)
    while True:
        try:
            claimed = await _claim_next_task()
            if claimed is None:
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL)
                continue
            db, task = claimed
            await _execute_claimed(db, task)
        except asyncio.CancelledError:
            logger.info("任务 worker 停止")
            break
        except Exception:
            logger.exception("worker 循环异常")
            await asyncio.sleep(2)
