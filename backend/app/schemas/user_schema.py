from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class UserProfileBase(BaseModel):
    name: Optional[str] = None
    profile_image_url: Optional[str] = None
    theme_preference: Optional[str] = "light"
    notification_enabled: Optional[bool] = True


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    profile_image_url: Optional[str] = None
    theme_preference: Optional[str] = None
    notification_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    profile: Optional[UserProfileBase] = None
    
    model_config = ConfigDict(from_attributes=True)
