"""
BeeGuardAI - User Settings Routes
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.db.mysql import get_db
from app.routes.auth import get_current_user

router = APIRouter(tags=["settings"])


class AlertSettings(BaseModel):
    enabled: bool = False
    email: Optional[str] = None
    hornetThreshold: int = 5


class ReportSettings(BaseModel):
    enabled: bool = False
    email: Optional[str] = None
    frequency: str = "weekly"
    dayOfWeek: int = 1
    hourOfDay: int = 8


class SettingsUpdate(BaseModel):
    alerts: Optional[AlertSettings] = None
    reports: Optional[ReportSettings] = None


@router.get("/api/settings")
async def get_settings(request: Request):
    """Get current user's settings"""
    user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM user_settings WHERE user_id = %s
    """, (user["user_id"],))

    settings = cursor.fetchone()
    conn.close()

    if not settings:
        # Return defaults
        return {
            "alerts": {
                "enabled": False,
                "email": user.get("email", ""),
                "hornetThreshold": 5
            },
            "reports": {
                "enabled": False,
                "email": user.get("email", ""),
                "frequency": "weekly",
                "dayOfWeek": 1,
                "hourOfDay": 8
            }
        }

    return {
        "alerts": {
            "enabled": bool(settings["alerts_enabled"]),
            "email": settings["alerts_email"] or user.get("email", ""),
            "hornetThreshold": settings["alerts_threshold"]
        },
        "reports": {
            "enabled": bool(settings["reports_enabled"]),
            "email": settings["reports_email"] or user.get("email", ""),
            "frequency": settings["reports_frequency"],
            "dayOfWeek": settings["reports_day_of_week"],
            "hourOfDay": settings["reports_hour_of_day"]
        }
    }


@router.put("/api/settings")
async def update_settings(data: SettingsUpdate, request: Request):
    """Update current user's settings"""
    user = get_current_user(request)

    conn = get_db()
    cursor = conn.cursor()

    # Check if settings exist
    cursor.execute("SELECT id FROM user_settings WHERE user_id = %s", (user["user_id"],))
    existing = cursor.fetchone()

    if existing:
        # Update existing settings
        updates = []
        values = []

        if data.alerts:
            updates.extend([
                "alerts_enabled = %s",
                "alerts_email = %s",
                "alerts_threshold = %s"
            ])
            values.extend([
                data.alerts.enabled,
                data.alerts.email,
                data.alerts.hornetThreshold
            ])

        if data.reports:
            updates.extend([
                "reports_enabled = %s",
                "reports_email = %s",
                "reports_frequency = %s",
                "reports_day_of_week = %s",
                "reports_hour_of_day = %s"
            ])
            values.extend([
                data.reports.enabled,
                data.reports.email,
                data.reports.frequency,
                data.reports.dayOfWeek,
                data.reports.hourOfDay
            ])

        if updates:
            values.append(user["user_id"])
            cursor.execute(f"""
                UPDATE user_settings SET {', '.join(updates)} WHERE user_id = %s
            """, tuple(values))
    else:
        # Insert new settings
        cursor.execute("""
            INSERT INTO user_settings (
                user_id, alerts_enabled, alerts_email, alerts_threshold,
                reports_enabled, reports_email, reports_frequency, reports_day_of_week, reports_hour_of_day
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user["user_id"],
            data.alerts.enabled if data.alerts else False,
            data.alerts.email if data.alerts else None,
            data.alerts.hornetThreshold if data.alerts else 5,
            data.reports.enabled if data.reports else False,
            data.reports.email if data.reports else None,
            data.reports.frequency if data.reports else "weekly",
            data.reports.dayOfWeek if data.reports else 1,
            data.reports.hourOfDay if data.reports else 8
        ))

    conn.close()

    return {"success": True, "message": "Settings updated"}
