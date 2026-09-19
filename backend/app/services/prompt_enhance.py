# 中文 prompt 增强服务：底模 CLIP 对纯中文基本不理解，须在发送前增强为"中文原意+英文风格关键词"
import json
import logging
import re

import httpx

from app.services import model_service

logger = logging.getLogger("studio.prompt_enhance")

# ASCII（含字母数字及常见英文提示词符号）占比高于该阈值视为"主要是英文"，不增强
_ASCII_THRESHOLD = 0.8

# 指令式口吻：命令动词开头，或含"一张/展示图"等需求描述词 —— 说明用户写的是需求而非画面本身
_INSTRUCTION_RE = re.compile(
    r"^(请|麻烦|帮我|给我|帮忙)?(生成|画|绘制|来一张|做一张?|出一张?|制作|设计)"
    r"|一张|展示图|效果图|高清图"
)

# 内置中文关键词 → 英文映射表（翻译模型不可用时的回退，可按需扩展）
KEYWORD_MAP = {
    "水墨": "ink wash painting",
    "海报": "poster",
    "插画": "illustration",
    "风景": "landscape",
    "人物": "portrait",
    "城市": "city",
    "动物": "animal",
    "山": "mountains",
    "花": "flowers",
    "夜景": "night scene",
    "夜晚": "night",
    "古风": "ancient chinese style",
    "二次元": "anime",
    "写实": "realistic",
    "卡通": "cartoon",
    "建筑": "architecture",
    "美食": "food",
    "赛博朋克": "cyberpunk",
    "森林": "forest",
    "大海": "ocean",
    "天空": "sky",
    "少女": "girl",
    "猫": "cat",
    "狗": "dog",
    "龙": "dragon",
    "樱花": "cherry blossoms",
    "雪": "snow",
    "日落": "sunset",
    "奇幻": "fantasy",
    "科幻": "sci-fi",
}

# 通用正向质量后缀
_QUALITY_SUFFIX = "high quality, detailed"

# 绘画/插画类判定词：命中时 negative 追加 photo 类负面词
_ART_WORDS = ("illustration", "painting", "art", "anime", "ink wash", "cartoon", "sketch")

# 命中绘画类时追加的负面词
_ART_NEGATIVE = "photo, realistic photo"


def is_mostly_english(prompt: str) -> bool:
    """ASCII 可打印字符占比高于阈值 → 视为英文 prompt，无需增强"""
    if not prompt:
        return True
    ascii_chars = sum(1 for ch in prompt if ord(ch) < 128)
    return ascii_chars / len(prompt) >= _ASCII_THRESHOLD


def is_instruction_style(prompt: str) -> bool:
    """指令式需求（如"生成一张XX展示图"）而非画面描述"""
    return bool(_INSTRUCTION_RE.search(prompt.strip()))


async def _translate_model(db) -> dict | None:
    """取模型库中已启用的翻译模型配置（meta 含 base_url/api_key/model_id）"""
    models = await model_service.list_models(db, "translate")
    enabled = [m for m in models if m["enabled"]]
    # 优先默认，否则取第一个
    for m in enabled:
        if m["is_default"]:
            return m
    return enabled[0] if enabled else None


async def _chat_via_model(model: dict, system: str, text: str, temperature: float = 0.2) -> str:
    """调 OpenAI 兼容 /chat/completions 单轮对话，失败抛异常"""
    meta = json.loads(model["meta"]) if isinstance(model["meta"], str) else model["meta"]
    base_url = (meta.get("base_url") or "").rstrip("/")
    model_id = meta.get("model_id")
    headers = {"Content-Type": "application/json"}
    if meta.get("api_key"):
        headers["Authorization"] = f"Bearer {meta['api_key']}"
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
        r = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


async def _translate_via_model(text: str, model: dict) -> str:
    """调 OpenAI 兼容接口把中文翻译成英文提示词"""
    return await _chat_via_model(
        model,
        "你是图像生成提示词翻译器。把用户中文翻译成简洁的英文图像生成提示词，"
        "输出英文短语组合，用逗号分隔，不要解释，不要输出中文。",
        text,
    )


# Z-Image 提示词改写：把"生成一张XX图"式指令改写为纯描述性画面提示词（保留专有名词）
_REWRITE_SYSTEM = (
    "你是图像生成提示词改写器。把用户的图像需求改写成一句纯描述性的中文画面提示词："
    "直接描述画面主体（书名号中的作品名与角色名等专有名词必须原样保留）、"
    "外观与铠甲/服装的颜色特征、动作姿态、场景背景、光影与画质。"
    "禁止出现\"生成、画一张、展示图、效果图\"等指令性或交付性措辞，"
    "不要解释，直接输出改写后的中文描述。"
)


async def rewrite_native(db, prompt: str) -> str:
    """Z-Image 原生中文底模的提示词优化：
    - 指令式需求（"生成一张XX展示图"）→ 用模型库翻译模型改写为描述性画面提示词
    - 已是描述性 prompt → 原样返回
    - 无可用模型 / 改写失败 → 回退原文（生图不因改写而失败）
    """
    if not is_instruction_style(prompt):
        return prompt
    try:
        model = await _translate_model(db)
        if not model:
            return prompt
        rewritten = await _chat_via_model(model, _REWRITE_SYSTEM, prompt, temperature=0.3)
        if rewritten and rewritten != prompt:
            logger.info("Z-Image 提示词改写: %s -> %s", prompt[:40], rewritten[:80])
            return rewritten
    except Exception as e:  # 改写失败不阻断生图
        logger.warning("Z-Image 提示词改写失败，使用原文: %s", e)
    return prompt


def _map_keywords(prompt: str) -> str:
    """内置关键词映射：逐词扫描中文 prompt，命中则替换为英文词，未命中保留原文"""
    parts = []
    for zh, en in KEYWORD_MAP.items():
        if zh in prompt and en not in parts:
            parts.append(en)
    return ", ".join(parts)


async def enhance(prompt: str, db, native_chinese: bool = False) -> str:
    """
    增强 prompt：中文 → "中文原意, 英文关键词, 质量词"。
    - native_chinese=True（Z-Image 等原生中文底模）时跳过翻译，原样返回
    - 英文 prompt 原样返回（仅补质量词）
    - 优先用模型库翻译模型翻译；失败/无配置时回退内置关键词映射
    """
    if not prompt.strip():
        return prompt

    # 原生中文底模（Qwen3 文本编码器）直接理解中文，翻译反而丢失细节
    if native_chinese:
        logger.info("原生中文底模，跳过翻译增强: %s", prompt[:50])
        return prompt

    # 英文 prompt 原样返回（不做翻译/映射）
    if is_mostly_english(prompt):
        return prompt

    translated = ""
    try:
        model = await _translate_model(db)
        if model:
            translated = await _translate_via_model(prompt, model)
            logger.info("prompt 翻译模型增强: %s -> %s", prompt[:30], translated[:80])
    except Exception as e:  # 翻译失败不阻断生图，回退关键词映射
        logger.warning("翻译模型调用失败，回退关键词映射: %s", e)
        translated = ""
    # 回退：内置关键词映射（命中至少一个关键词时只输出英文，中文正文不发给 SDXL）
    if not translated:
        mapped = _map_keywords(prompt)
        if mapped:
            translated = mapped
            logger.info("prompt 关键词映射增强: %s -> %s", prompt[:30], mapped[:80])

    if translated:
        enhanced = f"{translated}, {_QUALITY_SUFFIX}"
    else:
        # 无任何英文可用（映射零命中）时保留原文尽力而为，仅补质量词
        enhanced = f"{prompt}, {_QUALITY_SUFFIX}"
    return enhanced


def adjust_negative(enhanced_prompt: str, negative: str) -> str:
    """增强后的 prompt 命中绘画/插画类词时，negative 追加 photo 类负面词；否则原样返回"""
    if any(w in enhanced_prompt for w in _ART_WORDS):
        return f"{negative}, {_ART_NEGATIVE}"
    return negative
