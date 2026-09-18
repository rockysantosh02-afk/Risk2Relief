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

# In-memory SQLite async engine for isolated, high-speed domain testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def client():
    """Provides a synchronous TestClient for testing HTTP endpoints."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated async database session with initialized tables for domain tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
