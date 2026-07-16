from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
