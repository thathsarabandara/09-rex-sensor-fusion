from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.schemas.common import ResponseModel, ErrorDetail
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}")
            logger.debug(traceback.format_exc())
            req_id = getattr(request.state, "request_id", None)
            
            error_detail = ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected internal error occurred.",
                request_id=req_id
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "error": error_detail.model_dump()}
            )
