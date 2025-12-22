from fastapi import APIRouter, Depends
from security.auth import get_current_user
from services.logic import example_service
from pydantic_models.schemas import UserBase

router = APIRouter(
    prefix="/example",
    tags=["example"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_items(current_user: UserBase = Depends(get_current_user)):
    return {"message": "Hello World", "user": current_user.username}


@router.post("/process")
async def process_item(data: dict, current_user: UserBase = Depends(get_current_user)):
    return example_service.process_data(data)
