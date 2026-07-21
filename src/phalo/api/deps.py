"""Internal-API auth: a static service token shared with nuwa. Nothing in
Phalo is browser-facing — anything user-visible is served by nuwa with its
own authz (PH-5)."""

from fastapi import Header, HTTPException

from phalo.config import get_settings


async def require_service_token(
    x_phalo_token: str = Header(default=""),
) -> None:
    if x_phalo_token != get_settings().service_token:
        raise HTTPException(status_code=401, detail="Invalid service token")
