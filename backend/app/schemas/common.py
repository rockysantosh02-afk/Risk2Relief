"""Common Pydantic v2 schemas for pagination, sorting, and error envelopes."""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standardized pagination and sorting query parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=50, ge=1, le=500, description="Items per page")
    order_by: str = Field(default="created_at", description="Field name to sort by")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort direction")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list response wrapper."""
    items: List[T]
    total: int = Field(ge=0, description="Total count of items matching filter")
    page: int = Field(ge=1, description="Current page")
    limit: int = Field(ge=1, description="Page size limit")
    pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        limit: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> "PaginatedResponse[T]":
        effective_limit = limit if limit is not None else (page_size if page_size is not None else 50)
        pages = (total + effective_limit - 1) // effective_limit if effective_limit > 0 else 0
        return cls(items=items, total=total, page=page, limit=effective_limit, pages=pages)


class ErrorDetail(BaseModel):
    """Machine-readable error envelope."""
    error_code: str
    message: str
    detail: Optional[str] = None
