from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserPreferenceSchema(BaseModel):
    timezone: str = "UTC"
    email_notifications: bool = True
    push_notifications: bool = False
    daily_reminder: bool = True
    reminder_time: str = "09:00"
    weekly_report_enabled: bool = True

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_superuser: bool = False
    auth_provider: str
    timezone: str = "UTC"
    notification_preferences: Optional[UserPreferenceSchema] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50)
