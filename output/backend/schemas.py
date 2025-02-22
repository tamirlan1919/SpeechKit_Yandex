from typing import Optional

from pydantic import BaseModel, Field


class UserSettingsCreate(BaseModel):
    id: Optional[int] = Field(None)
    user_id: int
    selected_voice: str
    selected_speed: float
    format: str
    role: str
