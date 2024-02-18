import sqlite3



def create_db():
    # Подключение к базе данных SQLite
    
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()

    # Создание таблицы для хранения настроек пользователя
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        selected_voice TEXT,
                        selected_speed FLOAT,
                        format TEXT)
                ''')

    conn.commit()


def get_user_settings(user_id):
    conn = sqlite3.connect('user_settings.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT selected_voice, selected_speed, format FROM user_settings WHERE user_id = ?''', (user_id,))
    settings = cursor.fetchone()
    conn.close()
    if settings:
        return {
            'selected_voice': settings[0],
            'selected_speed': settings[1],
            'format': settings[2]
        }
    else:
        return None