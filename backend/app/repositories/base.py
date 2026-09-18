"""Generic Base Repository interface for data access.

Supports UUID and integer primary keys, async queries, CRUD, and pagination.
"""

import uuid
from typing import Generic, TypeVar, Type, Optional, Sequence, Union, Any, Dict
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing generic CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, item_id: Union[uuid.UUID, int, str]) -> Optional[ModelType]:
        """Fetch a single record by its primary key."""
        if isinstance(item_id, str):
            try:
                item_id = uuid.UUID(item_id)
            except ValueError:
                pass
        result = await self.session.execute(
            select(self.model).where(self.model.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> Sequence[ModelType]:
        """Fetch multiple records with limit/offset."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def count(self) -> int:
        """Count total records for this entity."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def create(self, entity: ModelType) -> ModelType:
        """Add and flush a new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Flush and refresh an updated entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Delete an existing entity."""
        await self.session.delete(entity)
        await self.session.flush()
