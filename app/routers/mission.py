from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Response, Depends

from app.dependencies import CurrentAdmin, CurrentUser, SessionDep
from app.models.mission import Mission
from app.schemas.mission import MissionCreate, MissionUpdate, MissionOut
from app.models.hero import Hero
from sqlmodel import select

router = APIRouter(prefix="/missions", tags=["missions"])

def get_existed_mission(
    mission_id: int,
    session: SessionDep,
) -> Mission:
    """
    return mission by id or raise HTTP_404_NOT_FOUND error if mission doesn't exists
    using get_existed_mission() to create reusable depedency parameter that validates mission exists before get, update, delete and returns the mission by id for use in the path operation function or raise HTTP_404_NOT_FOUND.
    """
    mission = session.get(Mission, mission_id)
    
    if not mission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Mission with id {mission_id} not found")

    return mission

# reusable dependency parameter for business get update delete by id
EXISTED_MISSION = Annotated[Mission, Depends(get_existed_mission)]  


@router.get("/{mission_id}", response_model=MissionOut, status_code=status.HTTP_200_OK)
def get_mission(
    mission: EXISTED_MISSION,
):
    """Get one mission by id. Public endpoint.If the hero doesn't exist, HTTP_404_NOT_FOUND is raised"""
    return mission


@router.post("", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
def create_mission(data: MissionCreate, session: SessionDep, user: CurrentUser):
    """Create a new mission. Requires authentication.
    Body: MissionCreate schema
    Returns MissionOut schema with status code 201."""
    hero = session.get(Hero, data.hero_id)

    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    mission = Mission(**data.model_dump())
    session.add(mission)
    session.commit()
    session.refresh(mission)

    return mission

@router.get("", response_model=list[MissionOut])
def list_missions(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
):
    """List all missions with pagination. Public endpoint."""

    missions = session.exec(
        select(Mission).offset(skip).limit(limit)
    ).all()

    return missions


@router.patch("/{mission_id}", response_model=MissionOut)
def update_mission(
    mission_id: int, 
    patch: MissionUpdate, # body schema
    session: SessionDep,
    user: CurrentUser, # authenticated user required.
    mission: EXISTED_MISSION # return mission by id or raise HTTP_404_NOT_FOUND 
    ):
    """Partial Update a mission.
     CurrentUser:Requires authentication user or raise HTTP_401_UNAUTHORIZED. 
     EXISTED_MISSION: validates mission exists and returns the mission by id or raise HTTP_404_NOT_FOUND doesn't exist.
     Body: MissionUpdate schema with optional fields.
     Returns MissionOut schema with status code 200.
     If the mission or given hero_id doesn't exist, HTTP_404_NOT_FOUND is raised."""

    update_data = patch.model_dump(exclude_unset=True) # Get only provided fields for update

    if "hero_id" in update_data:
        hero = session.get(Hero, update_data["hero_id"])
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")


    for key, value in update_data.items():
        setattr(mission, key, value)

    session.add(mission)
    session.commit()
    session.refresh(mission)

    return mission


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(
    mission_id: int,
    session: SessionDep,
    user: CurrentAdmin, # admin user required 
    mission: EXISTED_MISSION, # return mission by id or raise HTTP_404_NOT_FOUND
):
    """Delete a mission.
    CurrentAdmin: Requires authentication as admin or raise HTTP_401_UNAUTHORIZED if not authenticated, if authenticated without admin privileges raise HTTP_403_FORBIDDEN.
    EXISTED_MISSION: validates mission exists and returns the mission by id for deletion or raise HTTP_404_NOT_FOUND if mission or given hero_id doesn't exist.
    Response: 204 No Content with builded header Mission-Deleted: {mission_title} if successful.
    If the mission doesn't exist, HTTP_404_NOT_FOUND is raised."""

    response = Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Mission-Deleted": str(mission.title)
        }
    )
    session.delete(mission)
    session.commit()
    return response  

  

