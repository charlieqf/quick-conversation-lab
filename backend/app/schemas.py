from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Shared ---

class ScoringDimension(BaseModel):
    id: str
    label: str
    weight: int
    description: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Scenario Schemas ---

class ScenarioBase(BaseModel):
    title: str
    subtitle: str
    description: str
    tags: List[str]
    theme: str
    
    # Large content
    scriptContent: Optional[str] = Field(None, validation_alias="script_content", serialization_alias="scriptContent")
    workflow: Optional[str] = None
    knowledgePoints: Optional[str] = Field(None, validation_alias="knowledge_points", serialization_alias="knowledgePoints")
    scoringCriteria: Optional[str] = Field(None, validation_alias="scoring_criteria", serialization_alias="scoringCriteria")
    scoringDimensions: Optional[List[dict]] = Field([], validation_alias="scoring_dimensions", serialization_alias="scoringDimensions")
    
    # New field to match Frontend "Configuration" tab
    generationPrompt: Optional[str] = Field(None, validation_alias="generation_prompt", serialization_alias="generationPrompt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioRead(ScenarioBase):
    id: str
    lastUpdated: datetime = Field(validation_alias="last_updated", serialization_alias="lastUpdated")
    isDefault: bool = Field(False, validation_alias="is_default", serialization_alias="isDefault")
    author: Optional[str] = "System" # Computed field placeholder

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Role Schemas ---

class RoleBase(BaseModel):
    name: str
    nameCN: str = Field(validation_alias="name_cn", serialization_alias="nameCN")
    title: str
    description: str
    
    avatarSeed: Optional[str] = Field(None, validation_alias="avatar_seed", serialization_alias="avatarSeed")
    avatarImage: Optional[str] = Field(None, validation_alias="avatar_url", serialization_alias="avatarImage") # Map URL to Image field
    
    focusAreas: List[str] = Field([], validation_alias="focus_areas", serialization_alias="focusAreas")
    
    # Personality
    personality: Dict[str, int] # {hostility: 50, ...}
    
    systemPromptAddon: Optional[str] = Field(None, validation_alias="system_prompt_addon", serialization_alias="systemPromptAddon")
    generationPrompt: Optional[str] = Field(None, validation_alias="generation_prompt", serialization_alias="generationPrompt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class RoleCreate(RoleBase):
    personality: Optional[Dict[str, int]] = None
    # For creation, we accept flattened fields too to match frontend (optional)
    hostility: Optional[int] = 50
    verbosity: Optional[int] = 50
    skepticism: Optional[int] = 50

class RoleRead(RoleBase):
    id: str
    lastUpdated: datetime = Field(validation_alias="last_updated", serialization_alias="lastUpdated")
    isDefault: bool = Field(False, validation_alias="is_default", serialization_alias="isDefault")
    
    # Flattened Personality fields for Frontend Compat
    hostility: int = 50
    verbosity: int = 50
    skepticism: int = 50

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

# --- Auth & User Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any] # Return simplified user profile

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    role: str = "user"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str
    
    model_config = ConfigDict(from_attributes=True)

