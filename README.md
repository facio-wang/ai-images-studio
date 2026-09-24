<div align="center">

# AI Images Studio

**An open-source local text-to-image webUI — a one-stop AI image creation & management studio**

English | [简体中文](README.zh-CN.md)

Conversational text-to-image · Smart background removal · Model center · Asset library · Task queue · MCP Server

FastAPI + Vue3 + ComfyUI · Frontend & backend in one port · Docker one-click self-hosting

</div>

---

![Home Dashboard](docs/screenshots/home.png)

## ✨ Introduction

AI Images Studio is a **self-hosted** AI image creation hub: it integrates the ComfyUI generation engine, smart background removal, model management, an asset library and an async task queue into one web workbench, and exposes an **MCP Server** so external AI agents can drive it directly.

Design goals:

- **Conversation first** — generate images, remove backgrounds, and query assets in a single sentence; results are embedded right into the chat
- **Chinese-friendly prompting** — native support for Chinese-prompt base models (Z-Image Turbo GGUF + Qwen3 text encoder); instruction-style requests are automatically rewritten into descriptive scene prompts, while SDXL-family models go through an automatic translation pipeline
- **Low-friction deployment** — a single container runs frontend + backend + SQLite; the only external dependency is a ComfyUI instance
- **Observable & resilient** — a system status panel shows ComfyUI connectivity, GPU VRAM, system memory and queue in real time; when the generation service is down, both the generate page and the chat tell you immediately instead of failing silently
- **Hardware-tolerant async tasks** — polling-based waiting with smooth progress, transient-failure retry and generous per-task timeouts, so slow GPUs and low-power boxes (ARM mini PCs) are first-class citizens

## 🖼️ Screenshots

| Chat workbench | Generate studio |
| --- | --- |
| ![Chat](docs/screenshots/chat.png) | ![Generate](docs/screenshots/generate.png) |

| Matting toolbox | Task center with full prompt/parameter details |
| --- | --- |
| ![Matting](docs/screenshots/matting.png) | ![Tasks](docs/screenshots/tasks.png) |

| Asset library | Dashboard |
| --- | --- |
| ![Assets](docs/screenshots/assets.png) | ![Home](docs/screenshots/home.png) |

## 🧩 Modules

| # | Module | Route | Description |
|---|--------|-------|-------------|
| 1 | Dashboard | `#/creation/home` | Today's tasks / asset stats, **system status bar** (ComfyUI status light + GPU VRAM / memory meters, 30s refresh), recent works, quick entries |
| 2 | Chat workbench | `#/creation/chat` | Natural-language driven generate / matting / query; results embedded in messages with a **detail view** (full prompt / model / parameters); inline retry on failure; banner when the generation service is down |
| 3 | Generate | `#/creation/generate` | ComfyUI text-to-image: model selection (single-file checkpoints / GGUF quantized), size presets, steps/cfg/seed, LoRA, batch, poster text overlay |
| 4 | Matting | `#/creation/matting` | One-click background removal (u2net / bria-rmbg / birefnet) with a before/after compare slider |
| 5 | Model center | `#/studio/models` | Unified management of checkpoints / LoRA / translate / matting models: enable, set default, one-click sync from ComfyUI |
| 6 | Asset library | `#/manage/assets` | Browse / filter / download / delete all outputs; each asset's **detail dialog** shows the prompt and parameters it was generated with |
| 7 | Task center | `#/manage/tasks` | Async queue tracking (queued/running/done/failed), **detail dialog** (prompt / model / sampler / failure reason), auto + manual retry |
| 8 | Settings | `#/studio/settings` | Read-only runtime info (port / data dir / ComfyUI endpoint) + about |

> Login is a single token field: enter the `STUDIO_TOKEN` configured in `.env`. No username/password.

## 🎯 Highlights

### Conversational creation
- Rule-based intent routing (generate / matting / asset query / task query) with a `LlmAdapter` interface reserved for LLM orchestration
- Chinese instructions like "帮我生成一张赛博朋克城市夜景" → intent → prompt extraction → queued → results embedded back into the conversation
- Instruction-style prompts (e.g. "多啦A梦单人展示图") are automatically rewritten into **descriptive scene prompts** with proper nouns preserved, greatly improving character hit rate

### Prompt enhancement
- **Z-Image Turbo (native Chinese)**: instruction-style requests are rewritten into descriptive Chinese via the configured LLM; descriptive prompts pass through untouched
- **SDXL-family checkpoints**: Chinese → English keywords via the translate model; falls back to a built-in keyword map when unavailable
- Negative prompts are automatically extended with quality terms based on art/photo classification

### System status & fault tolerance
- `GET /api/system/status`: ComfyUI version, GPU devices & VRAM, system memory, running/queued jobs; degrades to `status=stopped` when ComfyUI is unreachable — never a 500
- **Pre-flight checks** on generate submission and chat generate-intents: if ComfyUI is down you get an immediate, explicit error (HTTP 503 / in-chat notice) instead of a silently spinning task
- **Hardware-tolerant waiting**: task polling survives transient failures (backoff retry, up to 10 consecutive failures before giving up), with smooth progress UI and per-task-type timeouts (matting 10 min, generate 15 min)
- **Crash-safe queue**: tasks orphaned in `running` state by a restart are automatically re-queued on worker startup
- SQLite WAL mode keeps API polling responsive even while a task is writing results

### Smart matting that respects low-power hardware
- Default model `u2net` (lightweight, CPU-friendly, seconds per image); `bria-rmbg` / `birefnet` offer higher quality but need GPU / strong CPUs
- Inference threads are capped (`MATTING_THREADS`, default 3) so the web event loop is never starved; inputs larger than `MATTING_MAX_SIDE` (default 2048) are downscaled for inference and the mask upscaled back — no more OOM on 4K images

### Async task queue
- SQLite-backed task table + asyncio worker; tasks survive process restarts
- Auto-retry on failure (default 2, configurable), unlimited manual retries

### MCP Server (agent integration)
The backend mounts `/mcp` (streamable-http) in the same process, authenticated like the main API, exposing 4 tools so external agents (Hermes, Claude, any MCP client) can drive generation, matting and queries.

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     docker compose : 8191                  │
│                                                            │
│  ┌──────────────── backend container (uvicorn) ─────────┐  │
│  │                                                      │  │
│  │  browser ──► / (SPA: Vue3 + art-design-pro, static)  │  │
│  │          ──► /api/*   FastAPI routes (Bearer auth)   │  │
│  │          ──► /files/* generated assets (static)      │  │
│  │          ──► /mcp      MCP streamable-http Server    │  │
│  │                                                      │  │
│  │  task worker (async queue) ──► ComfyUI(:8188) gen    │  │
│  │                             ──► rembg matting        │  │
│  │  SQLite + asset files ──► /app/data (volume)         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

- **Frontend**: Vue3 + TypeScript + Element Plus (based on [art-design-pro](https://github.com/Daymychen/art-design-pro)); build output is served by the backend — same port, same origin
- **Backend**: FastAPI + aiosqlite, unified `{code, msg, data}` responses, single-user Bearer token auth, built-in async task queue worker
- **Generation engine**: native ComfyUI HTTP API (`/object_info` `/prompt` `/history` `/view`) with two workflows:
  - `checkpoint`: CheckpointLoaderSimple (SDXL-family single-file models)
  - `z_image`: UnetLoaderGGUF + CLIPLoader(lumina2/Qwen3-4B) ([ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) quantized models, native Chinese)
- **Matting**: rembg (u2net / bria-rmbg / birefnet), CPU capable

## 📦 Quick Start

### Prerequisites

- Docker + Docker Compose (the deploy box does NOT need a GPU — compute lives on the ComfyUI side)
- A reachable [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance (same LAN recommended)
- (Optional) an OpenAI-compatible LLM endpoint for Chinese prompt translation/rewriting

### One-click deploy (Docker)

```bash
git clone https://github.com/facio-wang/ai-images-studio.git
cd ai-images-studio

cp .env.example .env
vim .env                      # set STUDIO_TOKEN to a strong random string, configure COMFYUI_URL
docker compose up -d --build  # build & start (first build compiles the frontend)
docker compose logs -f studio # tail logs
```

Open `http://<host>:8191`, enter `STUDIO_TOKEN` on the login page, done.

- Persistence: `./data` is mounted to `/app/data` (SQLite + all generated assets)
- If ComfyUI runs on the Docker host, set `COMFYUI_URL=http://host.docker.internal:8188` in `.env` (compose already includes `extra_hosts: host.docker.internal:host-gateway`)
- Health check: built-in `curl http://127.0.0.1:8191/`; check `docker compose ps` for the healthy state

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STUDIO_TOKEN` | `change-me` | Login token (single-user Bearer) — **change it to a strong random string** |
| `COMFYUI_URL` | `http://host.docker.internal:8188` | ComfyUI engine address |
| `COMFYUI_TIMEOUT` | `300` | Per-generation timeout in seconds |
| `STUDIO_DATA_DIR` | `/app/data` | Data dir (SQLite + assets) |
| `STUDIO_PORT` / `PORT` | `8191` | Service port |
| `REMBG_MODEL` | `u2net` | Default matting model (u2net / bria-rmbg / birefnet) |
| `MATTING_THREADS` | `3` | ONNX inference threads — lower it to keep the web loop responsive on small boxes |
| `MATTING_MAX_SIDE` | `2048` | Downscale inputs above this side before inference (mask upscaled back) |
| `STUDIO_ZIMAGE_TEXT_ENCODER` | `qwen_3_4b_fp8_mixed.safetensors` | Z-Image text encoder file (ComfyUI models/text_encoders) |
| `STUDIO_ZIMAGE_VAE` | `ae.safetensors` | Z-Image VAE file (ComfyUI models/vae) |
| `TASK_MAX_RETRY` | `2` | Auto-retry count for failed tasks |
| `WORKER_POLL_INTERVAL` | `1.0` | Worker poll interval (seconds) |

### Z-Image Turbo (recommended base model)

Place the following files in ComfyUI (install the [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) plugin first), then "Model center → Sync checkpoints":

| File | Directory |
|------|-----------|
| `z_image_turbo-Q4_K_M.gguf` (or other quant) | `ComfyUI/models/unet/` |
| `qwen_3_4b_fp8_mixed.safetensors` | `ComfyUI/models/text_encoders/` |
| `ae.safetensors` | `ComfyUI/models/vae/` |

Z-Image Turbo: 8-step distilled sampling (cfg=1.0, res_multistep/simple), Qwen3-4B text encoder understands Chinese prompts natively, runs on ~4GB VRAM — an excellent pick for low-end GPUs.

## 💻 Local Development

### Backend (port 8191)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env   # adjust STUDIO_TOKEN / COMFYUI_URL
uvicorn app.main:app --host 0.0.0.0 --port 8191
```

### Frontend (dev mode, Vite proxies /api → 127.0.0.1:8191)

```bash
cd frontend
npm install
npm run dev      # open http://localhost:3006, enter the backend's STUDIO_TOKEN on the login page
npm run build    # production build (vue-tsc type check + vite build) → dist/
```

## 🔌 MCP Integration

The backend exposes an MCP streamable-http endpoint at `/mcp`, authenticated like the main API (`Authorization: Bearer <STUDIO_TOKEN>`). Example MCP client config:

```json
{
  "mcpServers": {
    "ai-images-studio": {
      "transport": "streamable-http",
      "url": "http://127.0.0.1:8191/mcp",
      "headers": {
        "Authorization": "Bearer <your STUDIO_TOKEN>"
      }
    }
  }
}
```

Available tools:

| Tool | Parameters | Description |
|------|------------|-------------|
| `studio_generate_image` | `prompt, width, height, count` | Submit a text-to-image task and wait for completion |
| `studio_remove_bg` | `asset_id` | Remove background of an asset |
| `studio_list_assets` | `asset_type, limit` | List asset-library files |
| `studio_chat` | `message, session_id` | Conversational interaction (auto intent routing) |

## 📁 Project Layout

```
ai-images-studio/
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── api/        # routes (tasks / assets / generate / matting / models / chat / system)
│   │   ├── services/   # business (generate / task_service / chat_service / system_service / prompt_enhance / matting)
│   │   ├── models.py   # SQLite schema + query helpers
│   │   └── main.py     # app entry (static hosting + MCP mount + worker)
│   ├── tests/          # pytest
│   └── Dockerfile      # multi-stage build (node builds frontend → python runtime)
├── frontend/           # Vue3 frontend (art-design-pro base)
│   └── src/views/studio/   # workbench pages (home / chat / generate / matting / models / assets / tasks)
├── docs/screenshots/   # README screenshots
├── docker-compose.yml  # one-click deployment
├── .env.example        # env template (copy to .env)
└── LICENSE             # GPL-3.0
```

## 🔧 API Overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/system/status` | System status: ComfyUI connectivity / GPU / memory / queue (no auth) |
| `POST` | `/api/generate` | Submit a generation task (pre-flights ComfyUI) |
| `POST` | `/api/matting` | Submit a matting task (asset_id or image_base64) |
| `GET` | `/api/tasks` · `/api/tasks/{id}` | Task list / detail |
| `POST` | `/api/tasks/{id}/retry` | Manually retry a failed task |
| `GET` | `/api/assets` · `/api/assets/{id}` | Asset list / detail (detail includes source task params) |
| `DELETE` | `/api/assets/{id}` | Delete an asset (incl. disk files) |
| `GET`/`POST`/`PATCH`/`DELETE` | `/api/models` | Model center CRUD |
| `POST` | `/api/models/sync-checkpoints` | Sync checkpoint list from ComfyUI |
| `POST` | `/api/chat` | Chat message (generate intents pre-flight ComfyUI) |
| `GET` | `/api/chat/sessions` · `messages` · `quick-commands` | Sessions & quick commands |

All business endpoints require `Authorization: Bearer <STUDIO_TOKEN>`.

## ❓ FAQ

**Q: Everything says "generation service not started"?**
The workspace / chat page / top-bar "service" button all offer **one-click start**: with Docker deployments, double-click `scripts/host/install-autostart.bat` on the Windows host to register the resident launcher (adjust the ComfyUI path in `scripts/host/start_comfyui.bat` if needed) and set `COMFYUI_START_AGENT=http://host.docker.internal:8192` in `.env`. When the backend runs natively on Windows, set `COMFYUI_START_SCRIPT` instead. With neither configured, the button falls back to manual instructions. Still unreachable? Check ComfyUI at `COMFYUI_URL` (`curl http://<comfyui>:8188/system_stats`).

**Q: GGUF models don't show up after sync?**
Install the [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) plugin and restart ComfyUI; once `/object_info` exposes the `UnetLoaderGGUF` node, sync works.

**Q: Chinese prompts produce poor results / characters look wrong?**
- Use the Z-Image Turbo base model (native Chinese + automatic instruction rewriting)
- IP characters (tokusatsu/anime) are shallowly known by public base models — anchor with **character name + visual traits**, or train a dedicated LoRA

**Q: Why don't older assets show generation parameters?**
Details rely on the task link (`source_task_id`) and only apply to assets generated after this feature landed.

**Q: Does the deploy box need a GPU?**
No. Studio only orchestrates and stores; compute happens wherever ComfyUI runs.

**Q: Matting is slow or stuck in running?**
- The default `u2net` takes seconds-to-a-minute on CPU; `bria-rmbg` / `birefnet` are 1GB+ models and can be extremely slow on ARM mini PCs — switch back to u2net
- Occasional polling timeouts during inference are absorbed by the frontend's automatic retry; after a container restart, orphaned tasks are re-queued automatically

## 🛣️ Roadmap

- [ ] LLM-powered chat orchestration (`LlmAdapter` interface is ready)
- [ ] Image-to-image / inpainting
- [ ] Real-time generation progress (WebSocket)
- [ ] Multi-user & roles
- [ ] Asset tagging and smart search

## 🤝 Contributing

Issues and PRs are welcome! Before submitting:

- Backend changes: include pytest tests (`cd backend && pytest`)
- Frontend changes: make sure `npm run build` passes (includes vue-tsc)

## 📄 License

[GPL-3.0](./LICENSE) © 2026 facio

The frontend is built on [art-design-pro](https://github.com/Daymychen/art-design-pro) (MIT License) — thanks to the original author for the open-source contribution.
