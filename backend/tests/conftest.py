"""Pytest configuration and test fixtures for Risk2Relief."""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

# Ensure backend directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure test environment settings
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"
os.environ["SIMULATION_MODE"] = "true"
os.environ["ENABLE_HARDWARE_ACTUATION"] = "false"

from app.models import Base
from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import RoleEnum

# In-memory SQLite async engine with StaticPool for isolated, persistent in-process testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override connecting all FastAPI handlers to the isolated test SQLite session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Install dependency override on application
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated async database session with initialized tables for tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a synchronous TestClient for testing HTTP endpoints with isolated tables."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers_super_admin() -> dict:
    """Provides valid JWT Bearer authentication headers for a SUPER_ADMIN user."""
    token = create_access_token({
        "sub": "00000000-0000-0000-0000-000000000001",
        "username": "admin_test",
        "role": RoleEnum.SUPER_ADMIN.value,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_viewer() -> dict:
    """Provides valid JWT Bearer authentication headers for a read-only VIEWER user."""
    token = create_access_token({
        "sub": "00000000-0000-0000-0000-000000000002",
        "username": "viewer_test",
        "role": RoleEnum.VIEWER.value,
    })
    return {"Authorization": f"Bearer {token}"}
