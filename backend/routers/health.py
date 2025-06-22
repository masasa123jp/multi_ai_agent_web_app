"""
Liveness / readiness probe
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "live"}

@router.get("/ready", tags=["health"])
async def readiness() -> dict[str, str]:
    # ここで DB ping などを行っても良い
    return {"status": "ready"}
