from fastapi import APIRouter, Response, status
from config import settings
from database.core import check_connection
import redis.asyncio as redis

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    # Database Check
    db_status = "ok" if await check_connection() else "error"

    # Redis Check
    redis_status = "ok"
    try:
        r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        if not await r.ping():
            redis_status = "error"
        await r.close()
    except Exception:
        redis_status = "error"

    health_status = {
        "status": "ok" if db_status == "ok" and redis_status == "ok" else "error",
        "version": "1.0.0",
        "dependencies": {"database": db_status, "cache": redis_status},
    }

    if health_status["status"] == "error":
        return Response(
            content=str(health_status),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )

    return health_status
