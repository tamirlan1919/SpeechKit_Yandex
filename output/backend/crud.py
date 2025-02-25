from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from output.bot.database.models import UserSettings
from schemas import UserSettingsCreate


async def get_user_settings(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserSettings).filter(UserSettings.user_id == user_id))
    return result.scalars().first()


async def get_all_user_settings(db: AsyncSession):
    result = await db.execute(select(UserSettings))
    return result.scalars().all()


async def create_or_update_user_settings(db: AsyncSession, settings: UserSettingsCreate):
    existing_user = await get_user_settings(db, settings.user_id)

    if existing_user:
        existing_user.selected_voice = settings.selected_voice
        existing_user.selected_speed = settings.selected_speed
        existing_user.format = settings.format
        existing_user.role = settings.role
    else:
        new_user = UserSettings(**settings.dict())
        db.add(new_user)

    await db.commit()
    return existing_user or new_user
