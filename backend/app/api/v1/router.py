from fastapi import APIRouter

from backend.app.schemas.common import ApiResponse
from backend.app.schemas.health import HealthData

api_router = APIRouter()


@api_router.get("/health", response_model=ApiResponse[HealthData])
def health_check() -> ApiResponse[HealthData]:
    return ApiResponse(data=HealthData(status="ok"))
