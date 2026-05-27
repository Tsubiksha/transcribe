from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.user_schema import UserResponse, UserProfileUpdate
from app.core.security import get_current_user_id
from app.services.auth_service import update_user_email, create_or_update_profile, get_user_by_id

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=UserResponse)
def get_profile(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("", response_model=UserResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    if profile_data.email:
        existing = get_user_by_id(db, user_id)
        if existing and existing.email != profile_data.email:
            from app.services.auth_service import get_user_by_email
            if get_user_by_email(db, profile_data.email):
                raise HTTPException(status_code=400, detail="Email already registered")
        update_user_email(db, user_id, profile_data.email)
    
    if any(value is not None for value in [
        profile_data.name,
        profile_data.profile_image_url,
        profile_data.theme_preference,
        profile_data.notification_enabled,
    ]):
        create_or_update_profile(db, user_id, profile_data)
    
    user = get_user_by_id(db, user_id)
    return user
