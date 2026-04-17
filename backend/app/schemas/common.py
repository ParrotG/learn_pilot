from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class APIMessage(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Any | None = None


class HealthResponse(BaseModel):
    status: str
    app_name: str


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedModel(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime

