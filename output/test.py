import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from output.bot.database.models import Base, User, UserSettings  # импортируйте ваши модели

# --- Настройка подключения к PostgreSQL ---
PG_USER = 'post'
PG_PASSWORD = 'your_password'
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB = 'your_database'

pg_engine = create_engine("postgresql+psycopg2://postgres:linux1818@localhost:5433/yavoice")

PGSession = sessionmaker(bind=pg_engine)
pg_session = PGSession()

# Создаём таблицы в PostgreSQL по моделям
Base.metadata.create_all(pg_engine)



# --- Миграция данных из SQLite (user_settings.db) ---
conn_settings = sqlite3.connect('user_settings.db')
cursor_settings = conn_settings.cursor()

cursor_settings.execute("""
    SELECT id, user_id, selected_voice, selected_speed, format 
    FROM user_settings
""")
settings_data = cursor_settings.fetchall()

for row in settings_data:
    # Преобразование и проверка user_id
    user_id_val = row[1]
    if user_id_val in ['undefined', 'null']:
        continue
    try:
        user_id_int = int(user_id_val)
    except ValueError:
        continue

    # Проверяем, существует ли пользователь с таким user_id
    user_exists = pg_session.query(User).filter(User.user_id == user_id_int).first()
    if not user_exists:
        # Можно залогировать ошибку, пропустить запись или обработать по-другому
        print(f"Пользователь с user_id={user_id_int} не найден. Пропускаем запись.")
        continue

    setting = UserSettings(
        id=row[0],
        user_id=user_id_int,
        selected_voice=row[2],
        selected_speed=row[3],
        format=row[4]
    )
    pg_session.merge(setting)


pg_session.commit()
conn_settings.close()

# После миграции не забудьте закрыть сессию PostgreSQL
pg_session.close()
