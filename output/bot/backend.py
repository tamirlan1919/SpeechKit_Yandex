from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx

import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",'https://ui-telegrab-bot.vercel.app'],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Модель данных для передачи настроек пользователя
class UserSettings(BaseModel):
    user_id: str
    selected_voice: str
    selected_speed: float
    format: str
    role: str

# Функция для проверки существования пользователя в базе данных
def check_user_exists(user_id: int) -> bool:
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

async def notify_bot(user_id, selected_voice, selected_speed, role):
    bot_url = "http://localhost:3000/send_notification"
    payload = {
        "user_id": user_id,
        "selected_voice": selected_voice,
        "selected_speed": selected_speed,
        "role": role
    }
    async with httpx.AsyncClient() as client:
        await client.post(bot_url, json=payload)

# Обработчик для сохранения настроек пользователя
@app.post("/save_settings")
async def save_settings(settings: UserSettings):
    print(settings)
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()

    # Проверяем существование пользователя в базе данных
    user_exists = check_user_exists(settings.user_id)

    if user_exists:
        # Обновляем настройки пользователя
        cursor.execute('''UPDATE user_settings 
                          SET selected_voice = ?, selected_speed = ?, format = ?, role = ?
                          WHERE user_id = ?''',
                       (settings.selected_voice, settings.selected_speed, settings.format, settings.role, settings.user_id))
    else:
        # Добавляем новую запись о пользователе
        cursor.execute('''INSERT INTO user_settings (user_id, selected_voice, selected_speed, format,role)
                          VALUES (?, ?, ?, ?, ?)''',
                       (settings.user_id, settings.selected_voice, settings.selected_speed, settings.format, settings.role))
    conn.commit()
    conn.close()
    await notify_bot(settings.user_id, settings.selected_voice, settings.selected_speed, settings.role)

    return {"message": "Настройки сохранены успешно"}



# Обработчик для получения настроек всех пользователей
@app.get("/get_settings")
async def get_all_settings():
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()

    # Получаем настройки всех пользователей
    cursor.execute("SELECT user_id, selected_voice, selected_speed, format , role FROM user_settings")
    all_settings = cursor.fetchall()

    conn.close()

    if all_settings:
        return [{"user_id": row[0], "selected_voice": row[1], "selected_speed": row[2], "format": row[3], "role": row[4] } for row in all_settings]
    else:
        return {"message": "Настройки не найдены"}


@app.get('/')
async def start():
    return {'Done'}
