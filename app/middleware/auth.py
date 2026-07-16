import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.USER_JWT_SECRET_KEY,
            algorithms=[settings.USER_JWT_ALGORITHM],
            issuer=settings.USER_JWT_ISSUER,
            audience=settings.USER_JWT_AUDIENCE,
        )
        if not payload.get("email_verified"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None
