"""
Base Pydantic schemas
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CoordinatesSchema(BaseSchema):
    latitude: float
    longitude: float
    altitude: Optional[float] = None


class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None