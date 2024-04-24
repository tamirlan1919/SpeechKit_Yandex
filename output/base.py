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

def create_bonus_day():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS bonus_day (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        count INTEGER)
                    ''')
    conn.commit()
    conn.close()

def create_bonus_ref():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS bonus_ref (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        count INTEGER)
                    ''')
    conn.commit()
    conn.close()

def create_ref_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ref_table (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        invited_user_id TEXT,
                        count_request_month INTEGER)
                    ''')
    conn.commit()
    conn.close()

def activity_today():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS activity_today (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        last_activity_date TEXT)
                    ''')
    conn.commit()
    conn.close()



def save_referral_invited(referral_id, user_id):

    user = get_user_ref_table(user_id)
    
    if user :
        return
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    bonus_ref = get_bonus_ref()
    cursor.execute("INSERT INTO ref_table (user_id, invited_user_id) VALUES (?, ?)", (user_id, referral_id))
    conn.commit()
    update_bonus(referral_id, bonus_ref)

    conn.close()

def update_bonus_invited(user_id, bonus):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET bonus = bonus + ? WHERE user_id = ?", (bonus, user_id))
    conn.commit()
    conn.close()


def update_request_status(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET status = 'sent' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_referral(user_id):
 
    user = get_user_ref_table(user_id)
    if user:
        return
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ref_table (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_user_ref_table(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM ref_table WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    print(f'вот наш user = {user_id} а вот что нашли {existing_user}')
    conn.close()
    if existing_user == None:
        return 
    return existing_user[0]



def create_ref_table_admin():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ref_table_admin (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        count_request_month INTEGER,
                        service TEXT 
                        )
                    ''')
    conn.commit()
    conn.close()


def get_invited_users(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ref_table WHERE invited_user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user[0]


def get_request_mon_for_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count_request_month  FROM ref_table WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    if existing_user == None:
        return 0
    return existing_user[0]




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


def count_new_users_last_month():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получаем текущую дату
    current_date = datetime.datetime.now()
    # Получаем первый день текущего месяца
    first_day_current_month = current_date.replace(day=1)
    # Получаем последний день прошлого месяца
    last_day_last_month = first_day_current_month - datetime.timedelta(days=1)
    # Форматируем дату прошлого месяца в формат YYYY-MM
    last_month = last_day_last_month.strftime("%Y-%m")

    # Выполняем запрос к базе данных, чтобы получить количество новых пользователей за прошлый месяц
    cursor.execute("SELECT COUNT(*) FROM my_users WHERE subscription_date LIKE ?", (f"{last_month}%",))
    new_users_last_month = cursor.fetchone()[0]

    conn.close()
    return new_users_last_month


def count_active_users_today():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Получаем текущую дату
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM activity_today WHERE last_activity_date = ?", (today,))
    active_users_count = cursor.fetchone()[0]
    conn.close()
    return active_users_count


def insert_or_update_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получаем текущую дату и время
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d")

    # Проверяем, существует ли пользователь с таким именем в базе данных
    cursor.execute("SELECT COUNT(*) FROM activity_today WHERE user_id = ?", (username,))
    user_exists = cursor.fetchone()[0]

    if user_exists:
        # Если пользователь существует, обновляем его последнюю активность
        cursor.execute("UPDATE activity_today SET last_activity_date = ? WHERE user_id = ?", (current_datetime, username))
    else:
        # Если пользователь не существует, вставляем новую запись
        cursor.execute("INSERT INTO activity_today (user_id, last_activity_date) VALUES (?, ?)", (username, current_datetime))

    conn.commit()
    conn.close()


def add_daily_requests():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Проверяем, существует ли запись для пользователя
    cursor.execute("SELECT * FROM my_users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Если запись существует, выполняем операцию обновления (UPDATE)
        cursor.execute("UPDATE my_users SET request_month = ? WHERE user_id = ?", (25, user_id))
    else:
        # Если запись не существует, выполняем операцию вставки (INSERT)
        cursor.execute("INSERT INTO my_users (user_id, request_month) VALUES (?, ?)", (user_id, 25))

    conn.commit()
    conn.close()



def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id,name FROM my_users")
    rows = cursor.fetchall()
    conn.close()
    return rows

#По умолчанию
# Function to add a new user to the users table
def insert_bonus():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Check if the user ID already exists in the database
        cursor.execute("SELECT * FROM bonus_day")
        existing_user = cursor.fetchone()
        # If the user already exists, return without inserting
        if existing_user:

            return

        # Insert the new user into the database
        cursor.execute("INSERT INTO bonus_day(count)  VALUES (25)")
        conn.commit()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


def insert_ref_bonus():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Check if the user ID already exists in the database
        cursor.execute("SELECT * FROM bonus_ref")
        existing_user = cursor.fetchone()
        # If the user already exists, return without inserting
        if existing_user:

            return

        # Insert the new user into the database
        cursor.execute("INSERT INTO bonus_ref(count)  VALUES (10)")
        conn.commit()
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()


#Обновление бонуса

def update_bonus(count):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE bonus_day SET count = ?", (count,))
    conn.commit()
    cursor.execute("UPDATE my_users SET request_month = ?", (count,))
    conn.commit()
    conn.close()


#Обновление реф бонуса
    

def update_bonus_ref(count):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE bonus_ref SET count = ?", (count,))
    conn.commit()
    conn.close()


#Получение бонуса за реф ссылку

def get_bonus_ref():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM bonus_ref ")
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user[0]


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

def get_admin_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM my_users WHERE  user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    conn.close()
    return existing_user[0]



def minus_one(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE my_users SET request_month = request_month - 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def count_blocked_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Подсчитываем количество заблокированных пользователей
    cursor.execute("SELECT COUNT(*) FROM my_users WHERE status = 'sent'")
    blocked_count = cursor.fetchone()[0]

    conn.close()
    return blocked_count