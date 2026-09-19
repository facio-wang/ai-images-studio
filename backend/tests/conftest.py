# pytest 配置：测试用独立数据目录，不污染开发数据
import asyncio
import os
import shutil
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["STUDIO_TOKEN"] = "test-token"
os.environ["STUDIO_DATA_DIR"] = tempfile.mkdtemp(prefix="studio-test-")
os.environ["COMFYUI_URL"] = "http://127.0.0.1:9"  # 必然不可达
# 测试用轻量抠图模型（bria-rmbg 体积大，下载耗时不适合 CI）
os.environ["REMBG_MODEL"] = "u2netp"

os.makedirs(os.path.join(os.environ["STUDIO_DATA_DIR"], "assets"), exist_ok=True)

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models import init_db  # noqa: E402

TOKEN = {"Authorization": "Bearer test-token"}


@pytest.fixture(scope="session", autouse=True)
def setup_data_dir():
    """会话级：确保测试数据目录干净"""
    settings.ensure_dirs()
    yield
    shutil.rmtree(os.environ["STUDIO_DATA_DIR"], ignore_errors=True)


@pytest_asyncio.fixture
async def client():
    """每用例一个 AsyncClient（app lifespan 由手动初始化代替）"""
    await init_db()
    # 清空任务表，避免上一用例残留 queued 任务干扰本用例的 worker 驱动
    import aiosqlite

    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("DELETE FROM tasks")
        await db.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def run_worker_once():
    """手动驱动 worker 单轮处理（不启动真实后台循环，测试可控）"""
    from app.services import task_service

    async def _run():
        task_service.register_handlers()
        claimed = await task_service._claim_next_task()
        if claimed is None:
            return None
        db, task = claimed
        await task_service._execute_claimed(db, task)
        return task

    return _run
