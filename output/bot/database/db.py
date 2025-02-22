from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from output.bot.config import DATABASE_URL
from .models import Base

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL)

# Создаём асинхронную сессию
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_all_tables():
    async with engine.begin() as conn:
        # Создаёт все таблицы, определённые в Base.metadata
        await conn.run_sync(Base.metadata.create_all)
    # Опционально: закрываем engine, если он больше не нужен
    await engine.dispose()




# Функция получения сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
