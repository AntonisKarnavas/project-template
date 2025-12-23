from fastapi import APIRouter, Response, status

from database.core import check_connection

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint - checks database connectivity."""
    db_status = "ok" if await check_connection() else "error"

    health_status = {
        "status": db_status,
        "version": "1.0.0",
        "dependencies": {"database": db_status},
    }

    if health_status["status"] == "error":
        return Response(
            content=str(health_status),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )

    return health_status
