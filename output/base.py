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
    
def create_users_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS my_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        name TEXT,
                        subscription_date TEXT,
                        count_symbol INTEGER,
                        request_month INTEGER,
                        unlimited TEXT,
                        status TEXT,
                        role TEXT)
                    ''')
    conn.commit()
    conn.close()

# Function to add a new user to the users table
def add_user(user_id, name ,subscription_date,count_symbol,request_month,unlimited,status,role):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Check if the user ID already exists in the database
        cursor.execute("SELECT * FROM my_users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()
        # If the user already exists, return without inserting
        if existing_user:

            return

        # Insert the new user into the database
        cursor.execute("INSERT INTO my_users (user_id, name, subscription_date, count_symbol, request_month, unlimited,status,role ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, name ,subscription_date,count_symbol,request_month,unlimited, status,role))
        conn.commit()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


# Функция для подсчета общего количества пользователей
def count_total_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM my_users")
    total_users = cursor.fetchone()[0]
    conn.close()
    return total_users


def get_all_user_ids():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM my_users")
    total_users = cursor.fetchall()
    print(total_users)
    conn.close()
    
    return total_users


# Функция для подсчета новых пользователей за текущий месяц
def count_new_users_this_month():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    current_month = datetime.datetime.now().strftime("%Y-%m")
    cursor.execute("SELECT COUNT(*) FROM my_users WHERE subscription_date LIKE ?", (f"{current_month}%",))
    new_users_this_month = cursor.fetchone()[0]
    conn.close()
    return new_users_this_month



def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id,name FROM my_users")
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_user_symbols(user_id, new_symbols):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET count_symbol = ? WHERE user_id = ?", (new_symbols, user_id))
    conn.commit()
    conn.close()


def get_symbols(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count_symbol FROM my_users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user


def update_user_request_month(user_id, new_request_month):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET request_month = ? WHERE user_id = ?", (new_request_month, user_id))
    conn.commit()
    conn.close()


def get_request_month(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT request_month FROM my_users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user


def get_unlimited_person(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT unlimited FROM my_users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user


def update_unlimited_on(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET unlimited = 'ON' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_unlimited_off(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET unlimited = 'OFF' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_role_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM my_users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user

def get_status_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM my_users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user


def update_role_user_admin(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET role = 'admin' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_role_user_person(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET role = 'user' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_status_kick(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET status = 'kick' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_status_join(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET status = 'join' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_admin_from_bd():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(role) FROM my_users WHERE role = 'admin'")
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user[0]



def minus_one(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET request_month = request_month - 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()