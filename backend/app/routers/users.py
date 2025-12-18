from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models import User
from .auth import get_current_active_user

router = APIRouter()

class UserProfileResponse(BaseModel):
    id: str
    username: str
    avatar_url: Optional[str] = None
    settings: Optional[dict] = None
    role: str = "user"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    settings: Optional[dict] = None

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(profile: UserUpdate, 
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_active_user)):
    
    # Refresh because current_user is detached or we want to be sure to modify attached
    user = db.merge(current_user)
    
    if profile.username:
        user.username = profile.username
    if profile.avatar_url:
        user.avatar_url = profile.avatar_url
    if profile.settings:
        user.settings = profile.settings
        
    db.commit()
    db.refresh(user)
    return user
