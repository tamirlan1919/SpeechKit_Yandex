import sqlite3
import datetime


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
    
# Функция для создания таблицы пользователей, если ее еще нет
def create_users_table():
    conn = sqlite3.connect('my_users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS my_users (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT, subscription_date TEXT)''')
    conn.commit()
    conn.close()

# Функция для добавления нового пользователя в базу данных
def add_user(user_id, subscription_date):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO my_users (user_id, subscription_date) VALUES (?, ?)", (user_id, subscription_date))
    conn.commit()
    conn.close()


# Функция для подсчета общего количества пользователей
def count_total_users():
    conn = sqlite3.connect('my_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    return total_users

# Функция для подсчета новых пользователей за текущий месяц
def count_new_users_this_month():
    conn = sqlite3.connect('my_users.db')
    cursor = conn.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_date LIKE ?", (f"{current_month}%",))
    new_users_this_month = cursor.fetchone()[0]
    conn.close()
    return new_users_this_month