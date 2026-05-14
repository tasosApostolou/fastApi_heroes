from pydantic import BaseModel, Field

class MissionCreate(BaseModel):
    title: str =  Field(min_length=5)
    difficulty: int = Field(ge=1, le=10)
    completed: bool = False
    hero_id: int

class MissionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5)
    difficulty: int | None = Field(default=None, ge=1, le=10)
    completed: bool | None = None
    hero_id: int | None = None    

class MissionOut(BaseModel):
    id: int
    title: str
    difficulty: int
    completed: bool
    hero_id: int    
