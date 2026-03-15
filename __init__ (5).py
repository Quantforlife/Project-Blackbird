from fastapi import Header, HTTPException, status
from app.core.config import settings


async def verify_api_key(x_api_key: str = Header(default="")):
    """Simple API key auth — replace with JWT in production."""
    if settings.debug:
        return  # Skip auth in debug mode for ease of development
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
