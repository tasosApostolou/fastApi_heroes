from sqlmodel import Field, SQLModel,Relationship
from app.models.hero import Hero


class Mission(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=5)
    difficulty: int = Field(ge=1, le=10)
    completed: bool = False
    hero_id: int = Field(foreign_key="hero.id") # foreign key to Hero table
    hero: Hero | None = Relationship(back_populates="missions") # relationship Many-to-One with Hero

