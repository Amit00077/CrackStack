from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AIProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = None
    models: list[str] = Field(default_factory=list)
    active_model: str = Field(..., min_length=1)
    is_enabled: bool = True


class AIProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[list[str]] = None
    active_model: Optional[str] = None
    is_enabled: Optional[bool] = None


class AIProviderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    api_key_preview: str
    base_url: Optional[str] = None
    models: list[str]
    active_model: str
    is_active: bool
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SetActiveProviderRequest(BaseModel):
    provider_id: str = Field(..., min_length=1)
    active_model: Optional[str] = None


class AIProviderListResponse(BaseModel):
    items: list[AIProviderResponse]
