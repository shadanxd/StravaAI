"""
Prompt builders for activity-level and period summaries.
"""
from __future__ import annotations

from typing import Any, Dict, List


def build_activity_system_prompt() -> str:
    return (
        "You are an endurance training assistant. Be concise and actionable. "
        "Use SI units, avoid medical advice, and flag anomalies cautiously."
    )


def build_activity_user_prompt(user: Dict[str, Any], activity: Dict[str, Any], recent_snippets: List[Dict[str, Any]] | None = None) -> str:
    profile_bits = [
        f"athlete: {user.get('username', 'n/a')}",
        f"sex: {user.get('sex', 'n/a')}",
        f"weight_kg: {user.get('weight', 'n/a')}",
        f"city: {user.get('city', 'n/a')}",
        f"country: {user.get('country', 'n/a')}",
    ]

    act_bits = [
        f"type: {activity.get('activity_type')}",
        f"name: {activity.get('name')}",
        f"distance_m: {activity.get('distance')}",
        f"moving_time_s: {activity.get('moving_time')}",
        f"elevation_gain_m: {activity.get('total_elevation_gain')}",
        f"avg_speed_mps: {activity.get('average_speed')}",
        f"avg_hr: {activity.get('average_heartrate')}",
        f"kudos: {activity.get('kudos_count')}",
        f"start_date: {activity.get('start_date')}",
    ]

    recent_txt = ""
    if recent_snippets:
        # Include at most 3 concise lines from recent trend snippets
        lines = []
        for s in recent_snippets[:3]:
            lines.append(
                f"{s.get('label', 'recent')} value={s.get('value')} count={s.get('count')}"
            )
        recent_txt = "\nRecent trend snippets:\n" + "\n".join(lines)

    return (
        "Athlete profile:\n- "
        + "\n- ".join(profile_bits)
        + "\n\nActivity details:\n- "
        + "\n- ".join(act_bits)
        + recent_txt
        + "\n\nTask: Return JSON with keys [summary(str), coach_tips(list[str], 2-3 items), tags(list[str])]."
    )


def build_summary_system_prompt() -> str:
    return (
        "You summarize an athlete's recent training. Be specific, short, and constructive. "
        "Use SI units and avoid medical claims."
    )


def build_summary_user_prompt(user: Dict[str, Any], analytics: Dict[str, Any]) -> str:
    return (
        "Athlete: {username} ({city}, {country}).\nDate range: {start} to {end}.\n"
        "Overview: total activities={ta}, distance_m={td}, time_s={tt}, elevation_m={te}.\n"
        "By sport: {by_sport}.\n"
        "Task: Return JSON with keys [summary, coach_tips(2-3), tags]."
    ).format(
        username=user.get("username", "n/a"),
        city=user.get("city", "n/a"),
        country=user.get("country", "n/a"),
        start=analytics.get("date_range", {}).get("start_date"),
        end=analytics.get("date_range", {}).get("end_date"),
        ta=analytics.get("summary", {}).get("total_activities", 0),
        td=analytics.get("summary", {}).get("total_distance", 0),
        tt=analytics.get("summary", {}).get("total_time", 0),
        te=analytics.get("summary", {}).get("total_elevation", 0),
        by_sport=analytics.get("by_sport", []),
    )


