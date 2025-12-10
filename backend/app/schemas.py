from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Shared ---

class ScoringDimension(BaseModel):
    id: str
    label: str
    weight: int
    description: Optional[str] = None

# --- Scenario Schemas ---

class ScenarioBase(BaseModel):
    title: str
    subtitle: str
    description: str
    tags: List[str]
    theme: str
    
    # Large content
    scriptContent: Optional[str] = Field(None, alias="script_content")
    workflow: Optional[str] = None
    knowledgePoints: Optional[str] = Field(None, alias="knowledge_points")
    scoringCriteria: Optional[str] = Field(None, alias="scoring_criteria")
    scoringDimensions: Optional[List[dict]] = Field([], alias="scoring_dimensions")
    
    # New field to match Frontend "Configuration" tab
    generationPrompt: Optional[str] = Field(None, alias="generation_prompt")

    class Config:
        populate_by_name = True

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioRead(ScenarioBase):
    id: str
    lastUpdated: datetime = Field(alias="last_updated")
    isDefault: bool = Field(False, alias="is_default")
    author: Optional[str] = "System" # Computed field placeholder

    class Config:
        populate_by_name = True
        orm_mode = True

# --- Role Schemas ---

class RoleBase(BaseModel):
    name: str
    nameCN: str = Field(alias="name_cn")
    title: str
    description: str
    
    avatarSeed: Optional[str] = Field(None, alias="avatar_seed")
    avatarImage: Optional[str] = Field(None, alias="avatar_url") # Map URL to Image field
    
    focusAreas: List[str] = Field([], alias="focus_areas")
    
    # Personality
    personality: Dict[str, int] # {hostility: 50, ...}
    
    # We need to flatten personality for frontend if it expects flat fields? 
    # Frontend types says: hostility: number; verbosity: number...
    # But DB stores JSON "personality". 
    # We might need a custom validator/property or change Client to accept JSON.
    # checking types.ts: Role has "hostility", "verbosity" at top level.
    # So we need to flatten it or change DB.
    # Let's keep DB JSON but output Flattened in Schema using "mode='before'" validator?
    # Or simplified: The Frontend currently expects top-level fields. 
    # Ideally, we should update Frontend to read from 'personality' object OR 
    # we do the mapping here. Mapping here is cleaner for "Parity".
    
    systemPromptAddon: Optional[str] = Field(None, alias="system_prompt_addon")
    generationPrompt: Optional[str] = Field(None, alias="generation_prompt")

    class Config:
        populate_by_name = True

class RoleCreate(RoleBase):
    # For creation, we accept flattened fields too to match frontend
    hostility: Optional[int] = 50
    verbosity: Optional[int] = 50
    skepticism: Optional[int] = 50

class RoleRead(RoleBase):
    id: str
    lastUpdated: datetime = Field(alias="last_updated")
    isDefault: bool = Field(False, alias="is_default")
    
    # Flattened Personality fields for Frontend Compat
    hostility: int = 50
    verbosity: int = 50
    skepticism: int = 50

    class Config:
        populate_by_name = True
        orm_mode = True
