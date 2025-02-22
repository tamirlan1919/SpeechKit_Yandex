from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from output.bot.database.db import engine
from output.bot.database.models import Base

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ui-telegrab-bot.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Подключаем маршруты
app.include_router(router)

# Создаём таблицы при запуске
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    await init_db()
