# 模型中心服务：四分区模型 CRUD + ComfyUI 底模同步
import json

from app.models import fetch_all, fetch_one

CATEGORIES = ("checkpoint", "lora", "translate", "matting")


async def list_models(db, category: str | None = None) -> list[dict]:
    """模型列表，可按分区过滤"""
    if category:
        return await fetch_all(
            db, "SELECT * FROM models WHERE category=? ORDER BY is_default DESC, id", (category,)
        )
    return await fetch_all(db, "SELECT * FROM models ORDER BY category, is_default DESC, id")


async def add_model(db, category: str, name: str, meta: dict | None = None) -> dict:
    """新增模型（enabled 默认开）"""
    cur = await db.execute(
        "INSERT OR IGNORE INTO models(category, name, meta) VALUES(?,?,?)",
        (category, name, json.dumps(meta or {}, ensure_ascii=False)),
    )
    if cur.lastrowid:
        return await get_model(db, cur.lastrowid)
    return await fetch_one(db, "SELECT * FROM models WHERE category=? AND name=?", (category, name))


async def get_model(db, model_id: int) -> dict | None:
    return await fetch_one(db, "SELECT * FROM models WHERE id=?", (model_id,))


async def update_model(db, model_id: int, fields: dict) -> dict | None:
    """更新模型：name 改名 / enabled 启停 / is_default 设默认 / meta"""
    model = await get_model(db, model_id)
    if not model:
        return None

    if "name" in fields and str(fields["name"]).strip():
        await db.execute("UPDATE models SET name=? WHERE id=?", (str(fields["name"]).strip(), model_id))

    if "enabled" in fields:
        await db.execute("UPDATE models SET enabled=? WHERE id=?", (int(bool(fields["enabled"])), model_id))
    if "is_default" in fields:
        # 设默认：同分区先清零再置一
        if fields["is_default"]:
            await db.execute(
                "UPDATE models SET is_default=0 WHERE category=?", (model["category"],)
            )
        await db.execute(
            "UPDATE models SET is_default=? WHERE id=?", (int(bool(fields["is_default"])), model_id)
        )
    if "meta" in fields:
        await db.execute(
            "UPDATE models SET meta=? WHERE id=?",
            (json.dumps(fields["meta"], ensure_ascii=False), model_id),
        )
    return await get_model(db, model_id)


async def delete_model(db, model_id: int) -> bool:
    cur = await db.execute("DELETE FROM models WHERE id=?", (model_id,))
    return bool(cur.rowcount)


async def get_default_model(db, category: str) -> dict | None:
    """取分区默认模型；无默认则取该分区第一个启用模型"""
    row = await fetch_one(
        db,
        "SELECT * FROM models WHERE category=? AND is_default=1 AND enabled=1",
        (category,),
    )
    if row:
        return row
    return await fetch_one(db, "SELECT * FROM models WHERE category=? AND enabled=1 LIMIT 1", (category,))


async def sync_checkpoints_from_comfyui(db) -> dict:
    """从 ComfyUI /object_info 同步底模分区（INSERT OR IGNORE，不覆盖已有配置）。
    同时同步 GGUF 扩散模型（Z-Image 等，meta 标记 model_type=z_image）"""
    from app.services.generate import list_diffusion_models, list_sd_models

    remote = await list_sd_models()

    added = 0
    for m in remote:
        name = m.get("model_name") if isinstance(m, dict) else str(m)
        if not name:
            continue
        cur = await db.execute(
            "INSERT OR IGNORE INTO models(category, name, meta) VALUES('checkpoint', ?, ?)",
            (name, json.dumps({"source": "comfyui"}, ensure_ascii=False)),
        )
        if cur.lastrowid:
            added += 1

    # GGUF 扩散模型（Z-Image Turbo 等）：UnetLoaderGGUF 未安装/为空时静默跳过
    added_zimage = 0
    try:
        ggufs = await list_diffusion_models()
    except Exception:
        ggufs = []
    for m in ggufs:
        name = m.get("model_name") if isinstance(m, dict) else str(m)
        if not name:
            continue
        cur = await db.execute(
            "INSERT OR IGNORE INTO models(category, name, meta) VALUES('checkpoint', ?, ?)",
            (
                name,
                json.dumps({"source": "comfyui", "model_type": "z_image"}, ensure_ascii=False),
            ),
        )
        if cur.lastrowid:
            added_zimage += 1

    total = await fetch_one(db, "SELECT COUNT(*) AS c FROM models WHERE category='checkpoint'")
    return {
        "added": added + added_zimage,
        "added_zimage": added_zimage,
        "total": total["c"],
        "fetched": len(remote),
    }


def infer_model_type(name: str, meta: dict | str | None = None) -> str:
    """推断底模工作流类型：meta.model_type 优先，名称含 z_image/zimage 兜底 → z_image，否则 checkpoint"""
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except (TypeError, ValueError):
            meta = {}
    if isinstance(meta, dict) and meta.get("model_type"):
        return str(meta["model_type"])
    lowered = (name or "").lower()
    if "z_image" in lowered or "zimage" in lowered:
        return "z_image"
    return "checkpoint"
