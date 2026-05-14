"""
Hero Model — SQLModel table definition.
"""


from sqlmodel import Field, SQLModel, Relationship


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=3)
    power: str = Field(min_length=3)
    level: int = Field(default=1, ge=1, le=100)
    active: bool = True
    missions: list["Mission"] = Relationship(back_populates="hero",    sa_relationship_kwargs={"cascade": "all, delete-orphan"}, # relationship One-to-Many with Mission, cascade deletes all related missions when a hero is deleted
)  
      


