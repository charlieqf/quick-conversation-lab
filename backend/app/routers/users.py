from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models import User

router = APIRouter()

class UserProfileResponse(BaseModel):
    id: str
    username: str
    avatar_url: Optional[str] = None
    settings: Optional[dict] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    settings: Optional[dict] = None

# For MVP, we assume a single "guest" or "admin" user if no Auth header is present.
# In a real app, we'd decode JWT here.
def get_current_user_id(db: Session):
    # Try to find default admin
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        # Auto-create admin
        user = User(username="admin", settings={"theme": "light"})
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(profile: UserUpdate, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if profile.username:
        user.username = profile.username
    if profile.avatar_url:
        user.avatar_url = profile.avatar_url
    if profile.settings:
        user.settings = profile.settings
        
    db.commit()
    db.refresh(user)
    return user
