from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, index=True, nullable=False) # Login ID
    avatar_url = Column(Text(4294967295), nullable=True) # URL path or Base64 data (LONGTEXT)
    settings = Column(JSON, nullable=True) # User-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("SessionRecord", back_populates="user")

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True) # Null = System
    is_default = Column(Boolean, default=False, index=True) # System Template
    
    title = Column(String(255), index=True)
    subtitle = Column(String(255))
    description = Column(Text)
    theme = Column(String(50)) # blue, purple, orange
    tags = Column(JSON) # List[str]
    
    # Large Content
    workflow = Column(Text)
    knowledge_points = Column(Text)
    scoring_criteria = Column(Text)
    scoring_dimensions = Column(JSON) # List[dict]
    
    # Source Content
    script_content = Column(Text) # Raw text/script
    generation_prompt = Column(Text) # Custom prompt used for generation
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    is_default = Column(Boolean, default=False, index=True)
    
    name = Column(String(100)) # English ID
    name_cn = Column(String(100), index=True) # Chinese Name
    title = Column(String(100))
    avatar_url = Column(Text(4294967295)) # Replaces Base64 (LONGTEXT)
    avatar_seed = Column(String(100)) # Fallback seed
    
    description = Column(Text)
    focus_areas = Column(JSON) # List[str]
    personality = Column(JSON) # {hostility, ...}
    
    # Prompting
    system_prompt_addon = Column(Text)
    generation_prompt = Column(Text)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SessionRecord(Base):
    __tablename__ = "session_records"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # Updated to strict UUID and FKs per plan
    scenario_id = Column(String(36), ForeignKey("scenarios.id"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False, index=True)
    
    score = Column(Integer, default=0)
    
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer, default=0)
    
    messages = Column(JSON, nullable=True)
    ai_analysis = Column(JSON, nullable=True)
    
    audio_url = Column(String(512), nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    # Optional: Relationships to Scenario/Role if needed for verification
    # scenario = relationship("Scenario")
    # role = relationship("Role")
