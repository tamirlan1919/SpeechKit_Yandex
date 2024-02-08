import sqlite3



def create_db():

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()

    # Создание таблицы для хранения настроек пользователя
    cursor.execute('''CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    selected_voice TEXT NOT NULL,
    selected_speed REAL NOT NULL,
    format TEXT NOT NULL
);
                    )''')

    conn.commit()
