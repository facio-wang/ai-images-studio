# 对话工作台服务：规则引擎版 AI 编排（留 LLM 适配器接口）
# P1 不接真实 LLM：意图识别用关键词路由到 生图/抠图/查询 能力
import logging

import aiosqlite

from app.models import fetch_all, fetch_one
from app.services import task_service

logger = logging.getLogger("studio.chat")

# 快捷指令 chips（前端展示用）
QUICK_COMMANDS = [
    {"label": "生成一张图", "text": "生成一张赛博朋克风格的城市夜景"},
    {"label": "帮我抠图", "text": "把最近的图抠图"},
    {"label": "看最近作品", "text": "看看最近的资产"},
    {"label": "任务进度", "text": "查询任务进度"},
]

# 意图关键词路由表（按优先级匹配）
INTENT_KEYWORDS = {
    "matting": ("抠图", "去背景", "透明底", "removebg", "rembg", "matting", "抠出"),
    "generate": ("生成", "画一张", "生一张", "画个", "生图", "画一", "来一张", "帮我画", "draw", "generate"),
    "query_assets": ("最近", "资产", "作品", "看看", "列表", "图库"),
    "query_tasks": ("任务", "进度", "队列", "状态"),
}


class LlmAdapter:
    """LLM 适配器接口：P2+ 接入真实大模型时实现本类并替换 RuleOrchestrator"""

    async def reply(self, session_id: int, message: str, context: dict) -> dict:
        raise NotImplementedError


class RuleOrchestrator:
    """规则引擎编排：关键词意图识别 → 触发任务/查询 → 组装 AI 回复"""

    def detect_intent(self, message: str) -> str:
        text = message.lower()
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(k in text for k in keywords):
                return intent
        return "unknown"

    async def handle(self, db: aiosqlite.Connection, session_id: int, message: str) -> dict:
        """处理用户消息，返回 {content, intent, task_id, asset_ids}"""
        intent = self.detect_intent(message)

        if intent == "generate":
            prompt = self._extract_prompt(message)
            # 海报文字类诉求（带文字/加文字/标题XX）：底模画不出可读文字，引导去生图页配置文字叠加
            if any(k in message for k in ("带文字", "加文字", "加上文字", "标题")):
                return {
                    "content": (
                        f"AI 底模画不出可读文字（会输出乱码），建议这样操作：到「生图」页先生成底图，"
                        f"再在「添加文字」折叠区配置文字内容（支持中英文、颜色、位置、背景衬条），"
                        f"即可得到带真实文字的海报。本次已按普通生图处理：「{prompt}」。"
                    ),
                    "intent": intent,
                    "task_id": None,
                    "asset_ids": [],
                }
            task = await task_service.create_task(db, "generate", {"prompt": prompt, "count": 1})
            return {
                "content": f"好的，已创建生图任务 #{task['id']}，正在排队执行：「{prompt}」。完成后可在资产库查看。",
                "intent": intent,
                "task_id": task["id"],
                "asset_ids": [],
            }

        if intent == "matting":
            asset = await self._latest_asset(db, "generate") or await self._latest_asset(db, "upload")
            if asset is None:
                return {
                    "content": "还没有可抠图的图片。请先在「生图」或上传一张图片，然后说「把这张抠图」。",
                    "intent": intent,
                    "task_id": None,
                    "asset_ids": [],
                }
            task = await task_service.create_task(
                db, "matting", {"asset_id": asset["id"], "model": "bria-rmbg"}
            )
            return {
                "content": f"收到，正在对最近的图片（资产 #{asset['id']}）执行抠图，任务 #{task['id']}。",
                "intent": intent,
                "task_id": task["id"],
                "asset_ids": [],
            }

        if intent == "query_assets":
            assets = await fetch_all(db, "SELECT id, type, labels FROM assets ORDER BY id DESC LIMIT 5")
            if not assets:
                content = "资产库还是空的，试试说「生成一张赛博朋克城市夜景」。"
            else:
                lines = [f"#{a['id']} [{a['type']}] {a['labels'] or '未命名'}" for a in assets]
                content = "最近的资产：\n" + "\n".join(lines)
            return {"content": content, "intent": intent, "task_id": None, "asset_ids": []}

        if intent == "query_tasks":
            tasks = await fetch_all(db, "SELECT id, type, status FROM tasks ORDER BY id DESC LIMIT 5")
            if not tasks:
                content = "当前没有任务记录。"
            else:
                lines = [f"#{t['id']} [{t['type']}] {t['status']}" for t in tasks]
                content = "最近的任务：\n" + "\n".join(lines)
            return {"content": content, "intent": intent, "task_id": None, "asset_ids": []}

        return {
            "content": (
                "我目前可以帮你：\n"
                "· 生图：说「生成一张……」（描述你想画的画面）\n"
                "· 抠图：说「把最近的图抠图」\n"
                "· 查询：说「看看最近的资产」或「查询任务进度」"
            ),
            "intent": "unknown",
            "task_id": None,
            "asset_ids": [],
        }

    def _extract_prompt(self, message: str) -> str:
        """从生图指令中提取 prompt（去掉常见指令前缀）"""
        text = message.strip()
        for prefix in ("帮我生成", "帮我画", "生成一张", "生成", "画一张", "画个", "来一张", "生一张"):
            if text.startswith(prefix):
                return text[len(prefix):].strip() or text
        return text

    async def _latest_asset(self, db, asset_type: str) -> dict | None:
        return await fetch_one(
            db, "SELECT * FROM assets WHERE type=? ORDER BY id DESC LIMIT 1", (asset_type,)
        )


def looks_like_image_intent(message: str) -> bool:
    """轻量预判：消息是否可能触发生图/抠图任务（用于 ComfyUI 预检，宁滥勿缺）"""
    text = message.lower()
    return any(
        k in text for k in ("生成", "画", "抠图", "去背景", "生图", "做一张", "出一张", "来一张", "draw", "generate")
    )


# 默认编排器（规则引擎版）；接入 LLM 时替换此实例
orchestrator = RuleOrchestrator()


async def get_or_create_session(db: aiosqlite.Connection, session_id: int | None) -> dict:
    """会话不存在则创建；未传 id 则新建"""
    if session_id:
        session = await fetch_one(db, "SELECT * FROM chat_sessions WHERE id=?", (session_id,))
        if session:
            return session
    cur = await db.execute("INSERT INTO chat_sessions(title) VALUES('新会话')")
    return await fetch_one(db, "SELECT * FROM chat_sessions WHERE id=?", (cur.lastrowid,))


async def list_sessions(db: aiosqlite.Connection) -> list[dict]:
    return await fetch_all(db, "SELECT * FROM chat_sessions ORDER BY id DESC LIMIT 50")


async def get_messages(db: aiosqlite.Connection, session_id: int) -> list[dict]:
    return await fetch_all(
        db, "SELECT * FROM chat_messages WHERE session_id=? ORDER BY id ASC", (session_id,)
    )


async def send_message(db: aiosqlite.Connection, session_id: int | None, message: str) -> dict:
    """发消息主流程：落用户消息 → 编排 → 落 AI 回复 → 返回"""
    session = await get_or_create_session(db, session_id)
    await db.execute(
        "INSERT INTO chat_messages(session_id, role, content) VALUES(?,?,?)",
        (session["id"], "user", message),
    )

    outcome = await orchestrator.handle(db, session["id"], message)

    asset_ids_str = ",".join(str(a) for a in outcome.get("asset_ids", []))
    cur = await db.execute(
        "INSERT INTO chat_messages(session_id, role, content, task_id, asset_ids) VALUES(?,?,?,?,?)",
        (session["id"], "assistant", outcome["content"], outcome.get("task_id"), asset_ids_str),
    )
    return {
        "session_id": session["id"],
        "message_id": cur.lastrowid,
        "content": outcome["content"],
        "intent": outcome["intent"],
        "task_id": outcome.get("task_id"),
        "asset_ids": outcome.get("asset_ids", []),
    }


def quick_commands() -> list[dict]:
    return QUICK_COMMANDS
