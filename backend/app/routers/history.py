from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import random

from ..database import get_db
from ..models import SessionRecord

router = APIRouter()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from ..database import get_db
from ..models import SessionRecord
from .users import get_current_user_id

router = APIRouter()

# --- Pydantic Schemas for API ---
class SessionBase(BaseModel):
    scenarioId: str = Field(alias="scenario_id")
    roleId: str = Field(alias="role_id")
    score: int
    durationSeconds: int = Field(alias="duration_seconds")
    messages: List[dict]
    aiAnalysis: Optional[dict] = Field(None, alias="ai_analysis")
    startTime: Optional[datetime] = Field(None, alias="start_time")
    endTime: Optional[datetime] = Field(None, alias="end_time")

    class Config:
        populate_by_name = True

class SessionCreate(SessionBase):
    @classmethod
    def validate_messages(cls, v):
        if len(v) > 500:
             raise ValueError('Too many messages')
        return v
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "scenario_id": "uuid...",
                "role_id": "uuid...",
                "score": 85,
                "duration_seconds": 120,
                "messages": [{"role": "user", "content": "start"}]
            }
        }

class SessionRead(SessionBase):
    id: str
    startTime: datetime = Field(alias="start_time")
    endTime: datetime = Field(alias="end_time")
    audioUrl: Optional[str] = Field(None, alias="audio_url")

    class Config:
        populate_by_name = True
        orm_mode = True

# --- Endpoints ---

@router.get("", response_model=List[SessionRead])
def read_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    # Filter by user
    sessions = db.query(SessionRecord).filter(
        SessionRecord.user_id == user_id
    ).order_by(SessionRecord.start_time.desc()).offset(skip).limit(limit).all()
    return sessions

@router.post("", response_model=SessionRead)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    
    db_session = SessionRecord(
        id=str(uuid.uuid4()),
        user_id=user_id,
        scenario_id=session.scenarioId,
        role_id=session.roleId,
        score=session.score,
        duration_seconds=session.durationSeconds,
        messages=session.messages,
        ai_analysis=session.aiAnalysis,
        start_time=session.startTime or datetime.utcnow(),
        end_time=session.endTime or datetime.utcnow()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    db_session = db.query(SessionRecord).filter(
        SessionRecord.id == session_id,
        SessionRecord.user_id == user_id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(db_session)
    db.commit()
    return {"ok": True}

@router.post("/seed")
def seed_test_data(db: Session = Depends(get_db)):
    """Inserts realistic test data for current user"""
    user_id = get_current_user_id(db)
    
    # Use real IDs from DB
    from ..models import Scenario, Role
    
    db_scenarios = db.query(Scenario).all()
    db_roles = db.query(Role).all()
    
    if not db_scenarios or not db_roles:
         # Fallback to placeholders if DB is empty to avoid crashing, 
         # but ideally the user should call /api/data/seed_defaults first.
         scenario_ids = ["1"]
         role_ids = ["1"]
    else:
        scenario_ids = [s.id for s in db_scenarios]
        role_ids = [r.id for r in db_roles]
    
    import random
    new_records = []
    
    for i in range(5):
        sid = str(uuid.uuid4())
        msgs = [
            {"id": f"{sid}_1", "role": "model", "type": "text", "content": """医生您好，我最近感觉胸口有点闷。"""},
            {"id": f"{sid}_2", "role": "user", "type": "text", "content": """这种情况持续多久了？"""},
            {"id": f"{sid}_3", "role": "model", "type": "text", "content": """大概两三天吧。"""}
        ]
        
        rec = SessionRecord(
            id=sid,
            user_id=user_id,
            scenario_id=random.choice(scenario_ids),
            role_id=random.choice(role_ids),
            score=random.randint(60, 95),
            duration_seconds=random.randint(60, 300),
            messages=msgs,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )
        db.add(rec)
        new_records.append(rec)
    
    db.commit()
    return {"message": f"Seeded {len(new_records)} records for user {user_id}"}

