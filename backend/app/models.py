# 数据层：SQLite（aiosqlite）表结构 + 访问助手
import aiosqlite

from app.config import settings

# 建表语句：tasks / assets / models / chat_sessions / chat_messages
_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,                -- generate | matting
    status      TEXT NOT NULL DEFAULT 'queued',  -- queued | running | done | failed
    params      TEXT NOT NULL DEFAULT '{}',   -- 任务参数 JSON
    result      TEXT NOT NULL DEFAULT '{}',   -- 结果 JSON（asset ids / 错误信息）
    error       TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retry   INTEGER NOT NULL DEFAULT 2,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS assets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    type       TEXT NOT NULL,                 -- generate | matting | upload
    file_path  TEXT NOT NULL,                 -- 相对 assets 目录的文件名
    thumb_path TEXT,
    filename   TEXT,
    source_task_id INTEGER,
    labels     TEXT NOT NULL DEFAULT '',      -- 逗号分隔标签
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,                -- checkpoint | lora | translate | matting
    name        TEXT NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    is_default  INTEGER NOT NULL DEFAULT 0,
    meta        TEXT NOT NULL DEFAULT '{}',   -- 附加信息 JSON（如 ComfyUI 侧文件名）
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(category, name)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL DEFAULT '新会话',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES chat_sessions(id),
    role        TEXT NOT NULL,                -- user | assistant
    content     TEXT NOT NULL,
    task_id     INTEGER,                      -- 触发的任务
    asset_ids   TEXT NOT NULL DEFAULT '',     -- 消息内嵌产物，逗号分隔
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
"""


async def get_db() -> aiosqlite.Connection:
    """打开数据库连接（FastAPI 依赖注入用，每请求一个连接）

    busy_timeout=10s：任务 worker 写库时读请求等待锁而不是立刻报错；
    WAL 模式在 init_db 统一开启（读写不互斥），避免推理长事务阻塞任务轮询。
    """
    settings.ensure_dirs()
    db = await aiosqlite.connect(settings.DB_PATH, timeout=10)
    db.row_factory = aiosqlite.Row
    try:
        yield db
        await db.commit()
    finally:
        await db.close()


async def init_db() -> None:
    """建表（幂等）+ 开启 WAL（读写并发，写锁不再阻塞 API 轮询）"""
    settings.ensure_dirs()
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript(_SCHEMA)
        await db.commit()


async def fetch_all(db: aiosqlite.Connection, sql: str, args: tuple = ()) -> list[dict]:
    rows = await (await db.execute(sql, args)).fetchall()
    return [dict(r) for r in rows]


async def fetch_one(db: aiosqlite.Connection, sql: str, args: tuple = ()) -> dict | None:
    row = await (await db.execute(sql, args)).fetchone()
    return dict(row) if row else None
