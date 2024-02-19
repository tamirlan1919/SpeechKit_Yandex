from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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

# Функция для проверки существования пользователя в базе данных
def check_user_exists(user_id: int) -> bool:
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Обработчик для сохранения настроек пользователя
@app.post("/save_settings")
async def save_settings(settings: UserSettings):
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()

    # Проверяем существование пользователя в базе данных
    user_exists = check_user_exists(settings.user_id)

    if user_exists:
        # Обновляем настройки пользователя
        cursor.execute('''UPDATE user_settings 
                          SET selected_voice = ?, selected_speed = ?, format = ?
                          WHERE user_id = ?''',
                       (settings.selected_voice, settings.selected_speed, settings.format, settings.user_id))
    else:
        # Добавляем новую запись о пользователе
        cursor.execute('''INSERT INTO user_settings (user_id, selected_voice, selected_speed, format)
                          VALUES (?, ?, ?, ?)''',
                       (settings.user_id, settings.selected_voice, settings.selected_speed, settings.format))
    conn.commit()
    conn.close()
    
    return {"message": "Настройки сохранены успешно"}



