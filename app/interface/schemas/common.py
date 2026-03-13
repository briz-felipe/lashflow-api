from typing import Generic, TypeVar, List
from app.interface.schemas.base import CamelModel

T = TypeVar("T")


class PaginatedResponse(CamelModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    per_page: int


class ErrorResponse(CamelModel):
    error: str
    message: str
    status_code: int
