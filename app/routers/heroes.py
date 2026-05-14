from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentAdmin, CurrentUser, SessionDep
from app.models.hero import Hero
from app.models.mission import Mission
from app.schemas.hero import HeroCreate, HeroOut, HeroUpdate
from sqlmodel import select
from typing import Annotated
from fastapi import Depends, HTTPException

router = APIRouter(prefix="/heroes", tags=["heroes"])


# ---- Depedencies for hero business rules ----- #

def get_existed_hero(
    hero_id: int,
    session: SessionDep,
) -> Hero:
    """
    using get_existed_hero() to create reusable depedency path parameter that validates hero exists before get, update, delete and returns the hero by id for use in the path operation function or raise HTTP_404_NOT_FOUND error if hero doesn't exists
    """
    hero = session.get(Hero, hero_id)
    
    if not hero:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Hero with id {hero_id} not found")

    return hero

EXISTED_HERO = Annotated[Hero, Depends(get_existed_hero)]
 
def get_completed_hero(
    hero: EXISTED_HERO,
    session: SessionDep,
) -> Hero:
    """
    using get_completed_hero() to create depedency that validates hero has no active missions before allowing deletion and returns the hero for use in the path operation function or raise http error 400 if hero has active missions
    """
    active_mission = session.exec(
        select(Mission).where(
            Mission.hero_id == hero.id,
            Mission.completed == False,
        )
    ).first()

    if active_mission:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete hero with active missions"       
        )
    return hero

COMPLETED_HERO = Annotated[Hero, Depends(get_completed_hero)]

@router.get("/{hero_id}", response_model=HeroOut, status_code=status.HTTP_200_OK)
def get_hero(hero: EXISTED_HERO):
    """Get a single hero by ID.
    If the hero doesn't exist, HTTP_404_NOT_FOUND is raised by dependency."""
    return hero


@router.get("", response_model=list[HeroOut])
def list_heroes(session: SessionDep, skip: int = 0, limit: int = 20):
    """List heroes with pagination."""
    heroes = session.exec(select(Hero).offset(skip).limit(limit)).all()
    return heroes


@router.post("", response_model=HeroOut, status_code=status.HTTP_201_CREATED)
def create_hero(data: HeroCreate, session: SessionDep, user: CurrentUser):
    """
    Create a new hero. Requires authentication (user:CurrentUser) or raise HTTP_401_UNAUTHORIZED error if not authenticated.
    Body: HeroCreate schema
    Returns HeroOut schema with status code 201.
    """
    hero = Hero(**data.model_dump())
    try:
        session.add(hero)
        session.commit()
        session.refresh(hero)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create hero") from e
    return hero




@router.patch("/{hero_id}", response_model=HeroOut, status_code=status.HTTP_200_OK)
def update_hero(
    patch: HeroUpdate,
    hero: EXISTED_HERO, # Validate hero exists or HTTP_404_NOT_FOUND error
    session: SessionDep,
    user: CurrentUser, # Validate user is authenticated or raise HTTP_401_UNAUTHORIZED error
):
    """
    Partial update: only provided fields are changed.
    Requires authentication user:CurrentUser or HTTP_401_UNAUTHORIZED.
    body: HeroUpdate schema with optional fields.
    Returns updated hero with status code 200.
    """
    try:
        for field, value in patch.model_dump(exclude_unset=True).items():
            setattr(hero, field, value)

        session.add(hero)
        session.commit()
        session.refresh(hero)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update hero") from e
    return hero


@router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hero(
    user: CurrentAdmin, # Validate user is admin
    hero: COMPLETED_HERO, # hero has no active missions
    session: SessionDep,
):
    """
    Delete a hero. Requires Admin as current user and hero must have no active missions.
    COMPLETED_HERO: dependency validates hero has no active missions and returns the hero for deletion or raise HTTP status 400 error if hero has active missions or HTTP_404_NOT_FOUND is raised if hero doesn't exist.
    CurrentAdmin: validate user is authenticated as admin. if not authenticated returns HTTP_401_UNAUTHORIZED error, if authenticated without admin privilleges HTTP_403_FORBIDDEN is raised.
    response: 204 No Content if successful. 
    """
    try:
        session.delete(hero)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete hero") from e




# @router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_hero(hero_id: int, session: SessionDep, user: CurrentAdmin):
#     """Delete a hero. Requires Admin as current user."""
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status.HTTP_404_NOT_FOUND, "Hero not found")
#     if not completedHero(hero, session):
#         raise HTTPException(
#             status_code=400,
#             detail="Cannot delete hero with active missions",
#         )
#     session.delete(hero)
#     session.commit()

# def completedHero(
#     hero: Hero,
#     session: SessionDep,
# ) -> bool: 
#     active_mission = session.exec(
#         select(Mission).where(
#             Mission.hero_id == hero.id,
#             Mission.completed == False,
#         )
#     ).first()
#     return active_mission is None

