"""
AI Insights Routes
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, Path
from fastapi.responses import JSONResponse

from app.auth.middleware import get_current_user
from app.ai.insight_service import InsightService
from app.utils.json_serializer import to_json_serializable


ai_router = APIRouter(prefix="/api/insights", tags=["insights"])


@ai_router.post("/activity/{activity_id}/generate")
async def generate_activity_insight(
    request: Request,
    activity_id: str = Path(..., description="Internal activity ID (Mongo ObjectId)"),
    force: bool = Query(False, description="Regenerate even if already present"),
):
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        service = InsightService()
        payload = await service.generate_activity_insights(user_id=user_id, activity_id=activity_id, force=force)
        return JSONResponse(to_json_serializable(payload))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@ai_router.get("/activity/{activity_id}")
async def get_activity_insight(
    request: Request,
    activity_id: str = Path(..., description="Internal activity ID (Mongo ObjectId)"),
):
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        service = InsightService()
        payload = await service.generate_activity_insights(user_id=user_id, activity_id=activity_id, force=False)
        return JSONResponse(to_json_serializable(payload))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch insights: {str(e)}")


@ai_router.post("/bulk/recent")
async def generate_recent_insights(
    request: Request,
    limit: int = Query(5, ge=1, le=20, description="Generate insights for N most recent without insights"),
):
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        service = InsightService()
        result = await service.generate_recent_activities_bulk(user_id=user_id, limit=limit)
        return JSONResponse(to_json_serializable(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk generation failed: {str(e)}")


@ai_router.get("/summary")
async def get_period_summary(
    request: Request,
    days_back: int = Query(30, ge=7, le=180, description="Lookback window for summary"),
):
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        service = InsightService()
        payload = await service.generate_period_summary(user_id=user_id, days_back=days_back)
        return JSONResponse(to_json_serializable(payload))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


