from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User, UserProfile
from app.schemas.user_schema import UserProfileUpdate
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.add(UserProfile(user_id=db_user.id, name=email.split("@")[0]))
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_or_update_profile(db: Session, user_id: int, profile_data: UserProfileUpdate) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    
    if profile_data.name is not None:
        profile.name = profile_data.name
    if profile_data.profile_image_url is not None:
        profile.profile_image_url = profile_data.profile_image_url
    if profile_data.theme_preference is not None:
        profile.theme_preference = profile_data.theme_preference
    if profile_data.notification_enabled is not None:
        profile.notification_enabled = profile_data.notification_enabled
    
    db.commit()
    db.refresh(profile)
    return profile


def update_user_email(db: Session, user_id: int, email: str) -> User:
    user = get_user_by_id(db, user_id)
    if user:
        user.email = email
        db.commit()
        db.refresh(user)
    return user
