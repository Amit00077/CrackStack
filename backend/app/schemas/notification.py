from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    is_read: bool
    channel: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationPreferenceResponse(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    weekly_report: bool = True
    streak_reminder: bool = True

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    weekly_report: Optional[bool] = None
    streak_reminder: Optional[bool] = None
