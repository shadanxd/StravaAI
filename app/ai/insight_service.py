"""
Insight orchestration service.
Builds context, calls AI provider, validates, and persists into DB.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Union
from bson import ObjectId

from app.ai.providers import AIClient
from app.ai.prompt_builder import (
    build_activity_system_prompt,
    build_activity_user_prompt,
    build_summary_system_prompt,
    build_summary_user_prompt,
)
from app.database.db_operations import (
    activities_collection,
    get_analytics_summary,
    get_user_by_strava_id,
)


def _coerce_insight_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    summary = str(raw.get("summary", "")).strip()
    tips = raw.get("coach_tips") or []
    if not isinstance(tips, list):
        tips = [str(tips)] if tips else []
    tips = [str(t).strip() for t in tips if t] or []
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)] if tags else []
    tags = [str(t).strip().lower() for t in tags if t]
    model = str(raw.get("model", "")).strip() or None
    return {
        "summary": summary[:280],
        "coach_tips": tips[:3],
        "tags": tags[:5],
        "model": model,
        "generated_at": datetime.utcnow(),
    }


class InsightService:
    def __init__(self, ai_client: Optional[AIClient] = None) -> None:
        self.ai = ai_client or AIClient()

    async def _find_activity_for_user(
        self, user_id: int, identifier: Union[str, int, ObjectId]
    ) -> Optional[Dict[str, Any]]:
        # Try Mongo ObjectId
        if isinstance(identifier, ObjectId):
            query = {"_id": identifier, "user_id": user_id}
            return await activities_collection.find_one(query)
        if isinstance(identifier, str):
            # Attempt ObjectId parsing
            try:
                oid = ObjectId(identifier)
                query = {"_id": oid, "user_id": user_id}
                doc = await activities_collection.find_one(query)
                if doc:
                    return doc
            except Exception:
                pass
            # Attempt numeric Strava ID
            try:
                sid = int(identifier)
                query = {
                    "user_id": user_id,
                    "$or": [
                        {"strava_activity_id": sid},
                        {"strava_id": sid},
                    ],
                }
                return await activities_collection.find_one(query)
            except Exception:
                return None
        if isinstance(identifier, int):
            query = {
                "user_id": user_id,
                "$or": [
                    {"strava_activity_id": identifier},
                    {"strava_id": identifier},
                ],
            }
            return await activities_collection.find_one(query)
        return None

    async def generate_activity_insights(
        self,
        user_id: int,
        activity_id: Union[str, int, ObjectId],
        force: bool = False,
    ) -> Dict[str, Any]:
        activity = await self._find_activity_for_user(user_id=user_id, identifier=activity_id)
        if not activity:
            raise ValueError("Activity not found or not owned by user")

        # Return cached insights unless forcing
        if not force and activity.get("insights"):
            return activity["insights"]

        user = await get_user_by_strava_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Minimal recent trend snippets could be fetched via get_trend_timeseries; keep MVP simple.
        system_prompt = build_activity_system_prompt()
        user_prompt = build_activity_user_prompt(user=user, activity=activity, recent_snippets=None)

        raw = await self.ai.generate_json(system_prompt, user_prompt)
        payload = _coerce_insight_payload(raw)

        await activities_collection.update_one(
            {"_id": activity["_id"]},
            {"$set": {"insights": payload, "updated_at": datetime.utcnow()}},
        )

        return payload

    async def generate_recent_activities_bulk(self, user_id: int, limit: int = 5) -> Dict[str, int]:
        cursor = activities_collection.find({"user_id": user_id, "insights": {"$exists": False}}).sort(
            "start_date", -1
        ).limit(limit)
        to_update: List[Dict[str, Any]] = await cursor.to_list(length=limit)
        generated = 0
        for act in to_update:
            try:
                await self.generate_activity_insights(user_id=user_id, activity_id=act["_id"], force=False)
                generated += 1
            except Exception:
                # Skip failures in MVP bulk
                continue
        return {"generated": generated, "requested": len(to_update)}

    async def generate_period_summary(self, user_id: int, days_back: int = 30) -> Dict[str, Any]:
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise ValueError("User not found")
        # Reuse existing analytics aggregation with explicit window
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        # Build analytics payload using existing helper within window
        analytics = {
            "date_range": {"start_date": start_date, "end_date": end_date},
            **(await get_analytics_summary(user_id=user_id, after=start_date, before=end_date)),
        }
        system_prompt = build_summary_system_prompt()
        user_prompt = build_summary_user_prompt(user=user, analytics=analytics)
        raw = await self.ai.generate_json(system_prompt, user_prompt)
        return _coerce_insight_payload(raw)


