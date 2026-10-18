from fastapi import Request, HTTPException


async def require_api_key(request: Request) -> None:
    config = getattr(request.app.state, "config", None)
    if not config or not config.api_key:
        return  # Authentication disabled when no API key is configured
    key = request.headers.get("X-API-Key", "")
    if key != config.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key.")
