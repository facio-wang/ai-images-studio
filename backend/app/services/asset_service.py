# 资产服务：资产入库 / 查询 / 删除 / 下载
import aiosqlite

from app.config import settings
from app.models import fetch_all, fetch_one


async def list_assets(
    db: aiosqlite.Connection,
    asset_type: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 40,
) -> dict:
    """分页查询资产列表，支持类型筛选与标签关键词"""
    where, args = [], []
    if asset_type:
        where.append("type=?")
        args.append(asset_type)
    if keyword:
        where.append("labels LIKE ?")
        args.append(f"%{keyword}%")
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    total = (await fetch_one(db, f"SELECT COUNT(*) AS c FROM assets {clause}", tuple(args)))["c"]
    items = await fetch_all(
        db,
        f"SELECT * FROM assets {clause} ORDER BY id DESC LIMIT ? OFFSET ?",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for item in items:
        item["url"] = _asset_url(item["file_path"])
        item["thumb_url"] = _asset_url(item["thumb_path"]) if item["thumb_path"] else item["url"]
    return {"total": total, "items": items, "page": page, "page_size": page_size}


async def get_asset(db: aiosqlite.Connection, asset_id: int) -> dict | None:
    item = await fetch_one(db, "SELECT * FROM assets WHERE id=?", (asset_id,))
    if item:
        item["url"] = _asset_url(item["file_path"])
        item["thumb_url"] = _asset_url(item["thumb_path"]) if item["thumb_path"] else item["url"]
        # 顺带关联源任务：详情弹窗展示生成时的完整提示词与参数
        if item.get("source_task_id"):
            task = await fetch_one(db, "SELECT * FROM tasks WHERE id=?", (item["source_task_id"],))
            if task:
                item["task"] = task
    return item


async def delete_asset(db: aiosqlite.Connection, asset_id: int) -> bool:
    """删除资产记录及磁盘文件（不存在返回 False）"""
    item = await fetch_one(db, "SELECT * FROM assets WHERE id=?", (asset_id,))
    if not item:
        return False
    for key in ("file_path", "thumb_path"):
        if item[key]:
            path = settings.ASSETS_DIR / item[key]
            if path.is_file():
                path.unlink(missing_ok=True)
    await db.execute("DELETE FROM assets WHERE id=?", (asset_id,))
    return True


async def add_asset(
    db: aiosqlite.Connection,
    asset_type: str,
    file_path: str,
    thumb_path: str | None = None,
    filename: str | None = None,
    labels: str = "",
    source_task_id: int | None = None,
) -> dict:
    """登记一条资产记录（上传场景使用）"""
    cur = await db.execute(
        "INSERT INTO assets(type, file_path, thumb_path, filename, labels, source_task_id)"
        " VALUES(?,?,?,?,?,?)",
        (asset_type, file_path, thumb_path, filename, labels, source_task_id),
    )
    return await get_asset(db, cur.lastrowid)


def _asset_url(filename: str) -> str:
    return f"{settings.ASSETS_URL_PREFIX}/{filename}"
