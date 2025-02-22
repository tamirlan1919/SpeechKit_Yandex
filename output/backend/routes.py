from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.db import get_db
from .schemas import UserSettingsCreate
from .crud import create_or_update_user_settings, get_all_user_settings
from .utils import notify_bot

router = APIRouter()


@router.post("/save_settings")
async def save_settings(settings: UserSettingsCreate, db: AsyncSession = Depends(get_db)):
    user = await create_or_update_user_settings(db, settings)
    await notify_bot(settings.user_id, settings.selected_voice, settings.selected_speed, settings.role)
    return {"message": "Настройки сохранены успешно"}


@router.get("/get_settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    users = await get_all_user_settings(db)
    if not users:
        raise HTTPException(status_code=404, detail="Настройки не найдены")
    return users


@router.get("/")
async def root():
    return {"message": "API работает!"}
