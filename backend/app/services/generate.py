# 生图服务：HTTP 调用原生 ComfyUI API（/object_info / /prompt / /history / /view）
# 支持两类工作流：
#   checkpoint —— CheckpointLoaderSimple（SDXL 系单文件底模）
#   z_image    —— UnetLoaderGGUF + Qwen3-4B 文本编码器（Z-Image Turbo GGUF 量化底模，原生中文）
import asyncio
import logging
import random
import uuid

import httpx

from app.config import settings

logger = logging.getLogger("studio.generate")

# txt2img 默认参数（可被任务 params 覆盖）
DEFAULTS = {
    "width": 1024,
    "height": 1024,
    "steps": 20,
    "cfg": 7.0,
    "seed": -1,  # -1 随机
    "count": 1,
}

# 工作流中 SaveImage 节点号（两类工作流统一为 "7"，用于从 history 取产物）
_SAVE_NODE = "7"

# 通用质量负面词（用户显式传非空 negative 时尊重用户值）
DEFAULT_NEGATIVE = (
    "blurry, low quality, overexposed, washed out, watermark, text, jpeg artifacts,"
    " worst quality, low resolution, deformed"
)

# turbo 系模型的固定采样参数（steps=4 + 高 cfg 会未收敛/过曝）
_TURBO_CFG = 1.5
_TURBO_MIN_STEPS = 8
_TURBO_SAMPLER = "dpmpp_sde"
_TURBO_SCHEDULER = "karras"

# Z-Image Turbo（蒸馏 8 步）：固定低 cfg + res_multistep/simple
_ZIMAGE_CFG = 1.0
_ZIMAGE_MIN_STEPS = 8
_ZIMAGE_SAMPLER = "res_multistep"
_ZIMAGE_SCHEDULER = "simple"


def adapt_params(checkpoint: str, steps: int, cfg: float, sampler_name: str, scheduler: str) -> dict:
    """按底模类型自适应采样参数：turbo 系强制低 cfg + dpmpp_sde/karras，普通模型夹取到安全范围"""
    if "turbo" in (checkpoint or "").lower():
        return {
            "steps": max(steps, _TURBO_MIN_STEPS),
            "cfg": _TURBO_CFG,
            "sampler_name": _TURBO_SAMPLER,
            "scheduler": _TURBO_SCHEDULER,
            "denoise": 1.0,
        }
    return {
        "steps": max(steps, 12),
        "cfg": min(max(cfg, 4.0), 12.0),
        "sampler_name": sampler_name,
        "scheduler": scheduler,
        "denoise": 1.0,
    }


def zimage_params(steps: int) -> dict:
    """Z-Image Turbo 蒸馏模型的固定采样参数（cfg=1，负向词不参与采样）"""
    return {
        "steps": max(steps, _ZIMAGE_MIN_STEPS),
        "cfg": _ZIMAGE_CFG,
        "sampler_name": _ZIMAGE_SAMPLER,
        "scheduler": _ZIMAGE_SCHEDULER,
        "denoise": 1.0,
    }


async def list_sd_models() -> list[dict]:
    """从 ComfyUI /object_info 拉取单文件底模列表，返回 [{"model_name": ...}]，失败抛异常"""
    info = await _object_info()
    names = info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get(
        "ckpt_name", [[]]
    )[0]
    return [{"model_name": n} for n in names]


async def list_diffusion_models() -> list[dict]:
    """从 ComfyUI /object_info 拉取 GGUF 扩散模型列表（UnetLoaderGGUF，需装 ComfyUI-GGUF 节点）"""
    info = await _object_info()
    entry = info.get("UnetLoaderGGUF")
    if not entry:
        return []
    names = entry.get("input", {}).get("required", {}).get("unet_name", [[]])[0]
    return [{"model_name": n} for n in names]


async def _object_info() -> dict:
    async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
        r = await client.get(f"{settings.COMFYUI_URL}/object_info")
        r.raise_for_status()
        return r.json()


def _lora_chain(
    loras: list[dict] | None,
    first_model_ref: list,
    first_clip_ref: list | None,
    with_clip: bool,
) -> tuple[dict, list, list | None]:
    """构建 LoRA 节点链（model 逐级串联；with_clip 时 clip 同步串联）。
    返回 (追加节点字典, 末端 model 引用, 末端 clip 引用或 None)"""
    nodes: dict = {}
    model_ref = first_model_ref
    clip_ref = first_clip_ref
    for i, lora in enumerate(loras or []):
        node_id = str(10 + i)
        strength = float(lora.get("strength", 1.0))
        if with_clip:
            nodes[node_id] = {
                "class_type": "LoraLoader",
                "inputs": {
                    "lora_name": lora["name"],
                    "strength_model": strength,
                    "strength_clip": strength,
                    "model": model_ref,
                    "clip": clip_ref,
                },
            }
            clip_ref = [node_id, 1]
        else:
            nodes[node_id] = {
                "class_type": "LoraLoaderModelOnly",
                "inputs": {"lora_name": lora["name"], "strength_model": strength, "model": model_ref},
            }
        model_ref = [node_id, 0]
    return nodes, model_ref, clip_ref


def _build_workflow(
    prompt: str,
    checkpoint: str,
    negative: str,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    seed: int,
    count: int,
    sampler_name: str = "euler",
    scheduler: str = "normal",
    loras: list[dict] | None = None,
) -> dict:
    """txt2img 最小 API workflow：CheckpointLoaderSimple → CLIPTextEncode×2 → KSampler → VAEDecode → SaveImage
    loras 非空时在 loader 与 KSampler 之间串 LoraLoader 链（model+clip 同步生效）"""
    clip: list = ["1", 1]
    model_ref: list = ["1", 0]
    workflow: dict = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
    }
    if loras:
        lora_nodes, model_ref, clip = _lora_chain(loras, ["1", 0], clip, with_clip=True)
        workflow.update(lora_nodes)
    workflow.update(
        {
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip}},
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": count},
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": model_ref,
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                },
            },
            "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
            "7": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "studio", "images": ["6", 0]},
            },
        }
    )
    return workflow


def _build_zimage_workflow(
    prompt: str,
    negative: str,
    unet_name: str,
    text_encoder: str,
    vae_name: str,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    seed: int,
    count: int,
    sampler_name: str,
    scheduler: str,
    loras: list[dict] | None = None,
) -> dict:
    """Z-Image Turbo API workflow（节点结构与 ComfyUI 官方模板一致）：
    UnetLoaderGGUF + CLIPLoader(lumina2/Qwen3-4B) + EmptySD3LatentImage + KSampler → VAEDecode → SaveImage
    loras 走 LoraLoaderModelOnly（DiT 专用，无 clip）"""
    workflow: dict = {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": unet_name}},
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": text_encoder, "type": "lumina2", "device": "default"},
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae_name}},
    }
    model_ref: list = ["1", 0]
    if loras:
        lora_nodes, model_ref, _ = _lora_chain(loras, model_ref, None, with_clip=False)
        workflow.update(lora_nodes)
    workflow.update(
        {
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
            "6": {
                "class_type": "EmptySD3LatentImage",
                "inputs": {"width": width, "height": height, "batch_size": count},
            },
            "8": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": model_ref,
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "latent_image": ["6", 0],
                },
            },
            "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
            "7": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "studio", "images": ["9", 0]},
            },
        }
    )
    return workflow


async def _wait_history(client: httpx.AsyncClient, prompt_id: str) -> dict:
    """轮询 /history/{prompt_id} 直到任务完成，超时抛异常"""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + settings.COMFYUI_TIMEOUT
    while loop.time() < deadline:
        r = await client.get(f"{settings.COMFYUI_URL}/history/{prompt_id}")
        r.raise_for_status()
        entry = r.json().get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI 执行出错: {status.get('messages')}")
            if entry.get("outputs"):
                return entry
        await asyncio.sleep(1)
    raise TimeoutError(f"ComfyUI 生图超时（{settings.COMFYUI_TIMEOUT}s）: {prompt_id}")


async def txt2img(
    prompt: str,
    checkpoint: str | None = None,
    width: int = DEFAULTS["width"],
    height: int = DEFAULTS["height"],
    steps: int = DEFAULTS["steps"],
    cfg: float = DEFAULTS["cfg"],
    seed: int = DEFAULTS["seed"],
    count: int = DEFAULTS["count"],
    negative: str = DEFAULT_NEGATIVE,
    model_type: str = "checkpoint",
    loras: list[dict] | None = None,
) -> list[bytes]:
    """提交 /prompt → 轮询 /history → /view 下载，返回图片字节列表。任何失败抛异常（调用方标 failed）
    model_type: checkpoint=SDXL 系单文件底模 / z_image=Z-Image Turbo GGUF（原生中文）"""
    if not checkpoint:
        raise ValueError("缺少 checkpoint：未指定底模且模型库无默认模型")
    if seed < 0:  # -1 随机
        seed = random.randint(0, 2**32 - 1)

    if model_type == "z_image":
        adapted = zimage_params(steps)
        workflow = _build_zimage_workflow(
            prompt,
            negative,
            checkpoint,
            settings.ZIMAGE_TEXT_ENCODER,
            settings.ZIMAGE_VAE,
            width,
            height,
            adapted["steps"],
            adapted["cfg"],
            seed,
            count,
            adapted["sampler_name"],
            adapted["scheduler"],
            loras,
        )
    else:
        # 按底模自适应采样参数（turbo 系强制低 cfg，普通模型夹取安全范围）
        adapted = adapt_params(checkpoint, steps, cfg, "euler", "normal")
        workflow = _build_workflow(
            prompt,
            checkpoint,
            negative,
            width,
            height,
            adapted["steps"],
            adapted["cfg"],
            seed,
            count,
            adapted["sampler_name"],
            adapted["scheduler"],
            loras,
        )

    async with httpx.AsyncClient(timeout=settings.COMFYUI_TIMEOUT, trust_env=False) as client:
        payload = {
            "prompt": workflow,
            "client_id": uuid.uuid4().hex,
        }
        r = await client.post(f"{settings.COMFYUI_URL}/prompt", json=payload)
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]

        entry = await _wait_history(client, prompt_id)
        images: list[bytes] = []
        for img in entry.get("outputs", {}).get(_SAVE_NODE, {}).get("images", []):
            r = await client.get(
                f"{settings.COMFYUI_URL}/view",
                params={
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                },
            )
            r.raise_for_status()
            images.append(r.content)

    logger.info(
        "ComfyUI 生图完成: model_type=%s, %d 张, prompt=%s", model_type, len(images), prompt[:50]
    )
    if not images:
        raise RuntimeError("ComfyUI 返回结果中无图片")
    return images
