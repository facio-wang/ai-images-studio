# 海报文字叠加服务：用 Pillow 在底图上渲染真实可读的中英文文字
# SDXL 底模无法画出可读文字，海报类图片采用「AI 底图 + 真实文字叠加」方案
import io
import logging
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("studio.text_render")

# 启动时扫描的字体目录（Dockerfile 安装 fonts-noto-cjk / fonts-dejavu-core）
FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", str(Path.home() / ".fonts")]

# CJK 字体文件名特征（优先 Noto Sans CJK 黑体，再兜底其他 CJK 字体）
_CJK_FILE_HINTS = ("notosanscjk", "wqy-microhei", "wqy-zenhei", "notoserifcjk", "cjk", "droidsansfallback")
# 英文备选字体
_LATIN_HINTS = ("dejavusans", "dejavusans", "liberation", "arial", "helvetica")

# CJK 字符区间（含中日韩统一表意文字、扩展A、假名、谚文、全角标点）
_CJK_RE = re.compile(r"[⺀-鿿㐀-䶿豈-﫿　-〿＀-￯가-힯]")

# 字体路径缓存（进程内只扫描一次）
_font_cache: dict[str, str] = {}


def _scan_font_dirs() -> list[Path]:
    """收集字体目录下所有候选字体文件"""
    files: list[Path] = []
    for d in FONT_DIRS:
        root = Path(d)
        if not root.is_dir():
            continue
        files.extend(p for p in root.rglob("*") if p.suffix.lower() in (".ttf", ".otf", ".ttc"))
    return files


def _pick(files: list[Path], hints: tuple[str, ...]) -> str | None:
    """按文件名特征（不区分大小写）挑第一个匹配的字体"""
    for f in files:
        low = f.name.lower()
        if any(h in low for h in hints):
            return str(f)
    return None


def discover_fonts() -> dict[str, str]:
    """自动发现并缓存 CJK / 拉丁字体路径；找不到 CJK 时抛清晰错误"""
    if _font_cache:
        return _font_cache
    files = _scan_font_dirs()
    cjk = _pick(files, _CJK_FILE_HINTS)
    latin = _pick(files, _LATIN_HINTS) or cjk
    if not cjk:
        raise RuntimeError(
            "未找到 CJK 字体文件：请安装 fonts-noto-cjk（Dockerfile 已包含），"
            f"扫描目录: {', '.join(FONT_DIRS)}"
        )
    if not latin:
        raise RuntimeError("未找到拉丁字体文件：请安装 fonts-dejavu-core（Dockerfile 已包含）")
    _font_cache["cjk"] = cjk
    _font_cache["latin"] = latin
    logger.info("文字渲染字体: cjk=%s latin=%s", cjk, latin)
    return _font_cache


def _has_cjk(text: str) -> bool:
    """是否包含 CJK 字符（自动判断语言用）"""
    return bool(_CJK_RE.search(text))


def _parse_color(value, fallback=(0, 0, 0, 255)) -> tuple:
    """解析颜色：支持 #RGB/#RRGGBB/#RRGGBBAA 与 (r,g,b,a) 元组"""
    if isinstance(value, (tuple, list)):
        vals = list(value)
        while len(vals) < 4:
            vals.append(255)
        return tuple(vals[:4])
    if not isinstance(value, str) or not value.strip():
        return fallback
    s = value.strip().lstrip("#")
    try:
        if len(s) == 3:
            return tuple(int(c * 2, 16) for c in s) + (255,)
        if len(s) == 6:
            return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4)) + (255,)
        if len(s) == 8:
            return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4, 6))
    except ValueError:
        pass
    return fallback


def _resolve_coord(value, total: int) -> int:
    """坐标解析：支持像素整数或百分比字符串（如 "50%"，相对图宽/高）"""
    if isinstance(value, str) and value.strip().endswith("%"):
        try:
            return int(round(float(value.strip()[:-1]) / 100 * total))
        except ValueError:
            return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """按尺寸加载字体（缓存避免重复解析 ttc）"""
    key = f"{path}@{size}"
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def render_texts(image_bytes: bytes, texts: list[dict]) -> bytes:
    """在底图上叠加文字元素列表，返回 PNG bytes

    每个 text 元素字段：
      content: 文字内容（支持 \\n 换行）
      x/y: 像素或百分比字符串（"50%" 相对图宽/高）
      size: 字号（默认 48）
      color: 文字颜色（默认白）
      align: left/center/right（默认 left）
      bold: 是否用粗体字体
      stroke_color/stroke_width: 描边
      bg: 半透明底衬条颜色（如 "#000000CC"）或 null
      lang: cjk/latin，缺省按内容自动判断
    """
    fonts = discover_fonts()
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")
    # 在透明图层上绘制，最后合成，便于 bg 衬条半透明叠加
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    overlay_draw = ImageDraw.Draw(img)

    for item in texts or []:
        content = str(item.get("content", ""))
        if not content:
            continue
        lang = (item.get("lang") or ("cjk" if _has_cjk(content) else "latin")).lower()
        path = fonts["cjk"] if lang == "cjk" else fonts["latin"]
        size = int(item.get("size") or 48)
        bold = bool(item.get("bold"))
        # 粗体：优先同名 Bold 字体，找不到时加粗描边模拟
        if bold:
            bold_path = str(Path(path).with_name(Path(path).stem.replace("Regular", "Bold") + Path(path).suffix))
            if Path(bold_path).exists():
                path = bold_path
            else:
                bold_path = str(Path(path).with_name(Path(path).stem.replace("-Regular", "-Bold") + Path(path).suffix))
                if Path(bold_path).exists():
                    path = bold_path
        font = _load_font(path, size)
        color = _parse_color(item.get("color"), (255, 255, 255, 255))
        stroke_w = int(item.get("stroke_width") or 0)
        stroke_c = _parse_color(item.get("stroke_color"), (0, 0, 0, 255))
        x = _resolve_coord(item.get("x", 0), img.width)
        y = _resolve_coord(item.get("y", 0), img.height)
        align = (item.get("align") or "left").lower()
        anchor_map = {"center": "ma", "right": "ra"}
        anchor = anchor_map.get(align, "la")
        lines = content.split("\n")
        line_h = int(size * 1.3)

        # 半透明底衬条：先画在底图上（海报促销文案常用）
        bg = item.get("bg")
        if bg:
            bg_color = _parse_color(bg)
            line_spacing = int(size * 0.15)
            block_h = line_h * len(lines) + line_spacing * (len(lines) - 1)
            widths = [draw.textbbox((0, 0), ln, font=font)[2] for ln in lines]
            block_w = max(widths) + size * 0.5 if widths else 0
            bx = x - size * 0.25
            if align == "center":
                bx = x - block_w / 2
            elif align == "right":
                bx = x - block_w + size * 0.25
            overlay_draw.rectangle(
                [bx, y - size * 0.15, bx + block_w, y + block_h + size * 0.15], fill=bg_color
            )

        # 多行逐行绘制（Pillow multiline 文本用 textbbox 计算尺寸）
        for i, ln in enumerate(lines):
            draw.text(
                (x, y + i * line_h),
                ln,
                font=font,
                fill=color,
                anchor=anchor,
                stroke_width=stroke_w,
                stroke_fill=stroke_c,
            )

    out = Image.alpha_composite(img, layer)
    buf = io.BytesIO()
    out.save(buf, "PNG")
    return buf.getvalue()
