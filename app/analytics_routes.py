"""
Analytics Routes
Provides dashboard summary and trends endpoints using MongoDB aggregations.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.auth.middleware import get_current_user
from app.database.db_operations import (
    get_user_by_strava_id,
    get_analytics_summary,
    get_trend_timeseries,
)
from app.utils.json_serializer import to_json_serializable


analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@analytics_router.get("/dashboard")
async def analytics_dashboard(
    request: Request,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """Return a dashboard summary for the authenticated user.

    Includes: overall summary, per-sport breakdown, and milestone scaffolding (future).
    """
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        data = await get_analytics_summary(user_id=user_id, after=start_date, before=end_date)

        response = {
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "days_back": days_back,
            },
            "summary": data.get("summary", {}),
            "by_sport": data.get("by_sport", []),
            # Placeholder for future: milestones/progress can be derived or precomputed
            "milestones": to_json_serializable(user.get("milestones", [])),
        }

        return JSONResponse(to_json_serializable(response))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics dashboard: {str(e)}")


@analytics_router.get("/trends")
async def analytics_trends(
    request: Request,
    metric: str = Query(
        "distance",
        description="Metric to analyze: distance | time | elevation | calories | count",
    ),
    period: str = Query(
        "day",
        description="Aggregation period: day | week | month",
    ),
    activity_type: Optional[str] = Query(
        None, description="Filter by activity type (e.g., Run, Ride, Swim)"
    ),
    days_back: int = Query(90, ge=1, le=730, description="Lookback period in days"),
):
    """Return trends timeseries for the selected metric and period."""
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        timeseries = await get_trend_timeseries(
            user_id=user_id,
            metric=metric,
            after=start_date,
            before=end_date,
            period=period,
            activity_type=activity_type,
        )

        return JSONResponse(
            to_json_serializable(
                {
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "days_back": days_back,
                    },
                    "metric": metric,
                    "period": period,
                    "activity_type": activity_type,
                    "series": timeseries,
                }
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics trends: {str(e)}")


