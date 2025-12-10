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
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
from ..database import get_db
from ..models import SessionRecord
from .users import get_current_user_id

router = APIRouter()

# --- Pydantic Schemas for API ---
class SessionBase(BaseModel):
    scenarioId: str = Field(validation_alias="scenario_id", serialization_alias="scenarioId")
    roleId: str = Field(validation_alias="role_id", serialization_alias="roleId")
    score: int
    durationSeconds: int = Field(validation_alias="duration_seconds", serialization_alias="durationSeconds")
    
    # DB might store nullableJSON, handled by Optional with default
    messages: Optional[List[dict]] = []
    
    aiAnalysis: Optional[dict] = Field(None, validation_alias="ai_analysis", serialization_alias="aiAnalysis")
    startTime: Optional[datetime] = Field(None, validation_alias="start_time", serialization_alias="startTime")
    endTime: Optional[datetime] = Field(None, validation_alias="end_time", serialization_alias="endTime")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class SessionCreate(SessionBase):
    @classmethod
    def validate_messages(cls, v):
        if v and len(v) > 500:
             raise ValueError('Too many messages')
        return v
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra = {
            "example": {
                "scenarioId": "uuid...",
                "roleId": "uuid...",
                "score": 85,
                "durationSeconds": 120,
                "messages": [{"role": "user", "content": "start"}]
            }
        }
    )

class SessionRead(SessionBase):
    id: str
    startTime: datetime = Field(validation_alias="start_time", serialization_alias="startTime")
    endTime: datetime = Field(validation_alias="end_time", serialization_alias="endTime")
    audioUrl: Optional[str] = Field(None, validation_alias="audio_url", serialization_alias="audioUrl")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Endpoints ---

@router.get("", response_model=List[SessionRead])
def read_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user_id = get_current_user_id(db)
    # Filter by user
    sessions = db.query(SessionRecord).filter(
        SessionRecord.user_id == user_id
    ).order_by(SessionRecord.start_time.desc()).offset(skip).limit(limit).all()
    # Handle potentially None messages/analysis explicitly if Pydantic doesn't catch them
    # But Optional + default in Schema usually handles it unless output is None and field not optional.
    # We made them Optional.
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
         # Fallback to defaults to avoid crash
         scenario_ids = ["1"]
         role_ids = ["1"]
    else:
        scenario_ids = [s.id for s in db_scenarios]
        role_ids = [r.id for r in db_roles]
    
    import random
    from datetime import timedelta
    new_records = []
    
    # diverse start times within last 3 days
    base_time = datetime.utcnow()
    
    # Case 1: High Score - Fluent Conversation
    sid1 = str(uuid.uuid4())
    msgs1 = [
        {"id": f"{sid1}_1", "role": "user", "title": "医药代表", "type": "text", "content": "张主任您好，我是雅培的小王。今天想跟您交流一下内异症的保守治疗方案。"},
        {"id": f"{sid1}_2", "role": "model", "title": "张医生", "type": "text", "content": "你好小王，请坐。最近内异症患者确实不少。"},
        {"id": f"{sid1}_3", "role": "user", "title": "医药代表", "type": "text", "content": "是的主任。对于年轻有生育需求的患者，您在选择地诺孕素时，会担心由于不规则出血导致的依从性问题吗？"},
        {"id": f"{sid1}_4", "role": "model", "title": "张医生", "type": "text", "content": "会有这方面的顾虑。虽然我们都会提前教育，但还是有患者因为出血停药。"},
        {"id": f"{sid1}_5", "role": "user", "title": "医药代表", "type": "text", "content": "理解。这也正是达芙通的优势所在。临床数据显示，达芙通5-25天方案在保证疗效的同时，能显著降低不规则出血的发生率。"},
        {"id": f"{sid1}_6", "role": "model", "title": "张医生", "type": "text", "content": "这倒是个不错的思路，如果能减少出血，患者坚持用药的意愿会更高。"}
    ]
    rec1 = SessionRecord(
        id=sid1,
        user_id=user_id,
        scenario_id=scenario_ids[0] if scenario_ids else "1",
        role_id=role_ids[0] if role_ids else "1",
        score=92,
        duration_seconds=145,
        messages=msgs1,
        ai_analysis={"feedback": "开场定位清晰，准确捕捉到了医生的痛点（依从性）。在引入产品优势时过度自然，成功引起了医生的兴趣。", "strengths": ["提问技巧", "产品知识"], "improvements": ["可以增加更多数据支持"]},
        start_time=base_time - timedelta(hours=2),
        end_time=base_time - timedelta(hours=2) + timedelta(seconds=145)
    )
    db.add(rec1)
    new_records.append(rec1)

    # Case 2: Average Score - Missed Opportunity
    sid2 = str(uuid.uuid4())
    msgs2 = [
        {"id": f"{sid2}_1", "role": "user", "title": "医药代表", "type": "text", "content": "医生您好，我是来介绍达芙通的。"},
        {"id": f"{sid2}_2", "role": "model", "title": "李医生", "type": "text", "content": "我现在比较忙，即使说重点吧。"},
        {"id": f"{sid2}_3", "role": "user", "title": "医药代表", "type": "text", "content": "好的。达芙通治疗痛经效果很好，副作用也少。"},
        {"id": f"{sid2}_4", "role": "model", "title": "李医生", "type": "text", "content": "我知道它效果不错。但我现在习惯用地诺孕素。"},
        {"id": f"{sid2}_5", "role": "user", "title": "医药代表", "type": "text", "content": "但是达芙通更便宜啊，而且不抑制排卵。"}
    ]
    rec2 = SessionRecord(
        id=sid2,
        user_id=user_id,
        scenario_id=scenario_ids[0] if scenario_ids else "1",
        role_id=role_ids[1] if len(role_ids)>1 else role_ids[0],
        score=75,
        duration_seconds=60,
        messages=msgs2,
        ai_analysis={"feedback": "开场稍显仓促，未能有效建立连接。面对医生的拒绝，未能深入探询原因，而是直接抛出价格优势，显得针对性不强。", "strengths": ["反应速度"], "improvements": ["聆听技巧", "探询需求"]},
        start_time=base_time - timedelta(days=1),
        end_time=base_time - timedelta(days=1) + timedelta(seconds=60)
    )
    db.add(rec2)
    new_records.append(rec2)
    
    # Case 3: Short/Incomplete
    sid3 = str(uuid.uuid4())
    msgs3 = [
        {"id": f"{sid3}_1", "role": "user", "title": "医药代表", "type": "text", "content": "主任，打扰了。"},
        {"id": f"{sid3}_2", "role": "model", "title": "张医生", "type": "text", "content": "请进。"}
    ]
    rec3 = SessionRecord(
        id=sid3,
        user_id=user_id,
        scenario_id=scenario_ids[0] if scenario_ids else "1",
        role_id=role_ids[0] if role_ids else "1",
        score=0,
        duration_seconds=10,
        messages=msgs3,
        ai_analysis=None,
        start_time=base_time - timedelta(days=2),
        end_time=base_time - timedelta(days=2) + timedelta(seconds=10)
    )
    db.add(rec3)
    new_records.append(rec3)

    db.commit()
    return {"message": f"Seeded {len(new_records)} realistic records."}
