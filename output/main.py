import io
import aiohttp
import grpc
import pydub
import argparse
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import asyncio
from aiogram.types import Chat
from config import *
import yandex.cloud.ai.tts.v3.tts_pb2 as tts_pb2
import yandex.cloud.ai.tts.v3.tts_service_pb2_grpc as tts_service_pb2_grpc
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.web_app_info import WebAppInfo
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import tempfile
from base import *
from aiogram.utils.exceptions import ChatNotFound
import datetime
from state import *
from apscheduler.schedulers.background import BackgroundScheduler



API_TOKEN = TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())

state_bot = True

scheduler = BackgroundScheduler()
scheduler.start()


users_per_page = 3  # Установка количества пользователей на странице
create_db()
create_users_table()
create_ref_table()
create_bonus_day()
insert_bonus()
create_bonus_ref()
insert_ref_bonus()
activity_today()


users = get_all_users()

voice_descriptions = {
    'alena': 'Алёна 💅',
    'filipp': 'Филипп 👤',
    'ermil': 'Ермил 👤',
    'jane': 'Джейн 💅',
    'madirus': 'Мадирас 👤',
    'omazh': 'Омаж 👤',
    'zahar': 'Захар 👤',
    'dasha': 'Даша 💅',
    'julia': 'Юлия 💅',
    'lera': 'Лера 💅',
    'masha': 'Маша 💅',
    'marina': 'Марина 💅',
    'alexander': 'Александр 👤',
    'kirill': 'Кирилл 👤',
    'anton': 'Антон 👤'
}

def generate_voice_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    voices = list(voice_descriptions.keys())  # Получаем список ключей словаря
    for i in range(0, len(voices), 3):
        row = []
        for voice in voices[i:i+3]:
            description = voice_descriptions.get(voice, voice)  # Если описания нет, используйте сам голос
            row.append(types.InlineKeyboardButton(text=description, callback_data=f"voice_{voice}"))
        keyboard.row(*row)
    return keyboard



@dp.message_handler(commands=['start'], state="*")
async def handle_start(message: types.Message):
    if message.chat.type == "private":
        referal_id = None
        if len(message.text.split()) > 1:
            res = message.text.split()
            res = res[-1]
            res = res.replace('ref','')
            referal_id = res
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Прагласительная ссылка 🫂', callback_data='ref_link'))
        # Текст приветственного сообщения с эмодзи
        welcome_text = "Привет! Я бот, который может преобразовывать текст в речь. " \
                    "Просто отправь мне текст, и я создам для тебя голосовое сообщение! 🎤"
        # Отправляем текст и преобразуем его в речь
        if referal_id:
            save_referral_invited(referal_id, message.from_user.id)
            if message.from_user.username == None:
                add_user(message.from_user.id, message.from_user.first_name ,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),2500,10,'OFF','join','user')
            else:
                add_user(message.from_user.id, message.from_user.username ,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),2500,10,'OFF','join','user')
            await bot.send_message(message.chat.id, welcome_text,reply_markup=keyboard)
        else:
            
            save_referral(message.from_user.id)
            if message.from_user.username == None:
                add_user(message.from_user.id, message.from_user.first_name ,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),2500,10,'OFF','join','user')
            else:
                add_user(message.from_user.id, message.from_user.username ,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),2500,10,'OFF','join','user')
            await bot.send_message(message.chat.id, welcome_text,reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id,'бот работает в личных сообщениях')
# Обработчик нажатия на кнопку "Поиск по логину"
@dp.callback_query_handler(lambda call: call.data == "ref_link", state="*")
async def handle_ref_link(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    invited_users = get_invited_users(user_id=callback_query.message.chat.id )
    get_req = get_request_mon_for_user(user_id=callback_query.message.chat.id )
    count = get_bonus_ref()
    await bot.send_message(chat_id=callback_query.message.chat.id,text=REF_TEXT.format(count = count,users=invited_users,count2=get_req,url = f'https://t.me/fdfdfdsndslkv_bot?start=ref{callback_query.message.chat.id}'))
    

# Обработчик текстового сообщения с логином пользователя
@dp.message_handler(state=SearchUserState.InputUsername, content_types=types.ContentTypes.TEXT)
async def handle_ref_link(message: types.Message, state: FSMContext):
    username = message.text
    users = get_all_users()

    found_users = [(user_id, user_name) for user_id, user_name in users if username.lower() in user_name.lower()]

    if found_users:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for user_id, user_name in found_users:
            keyboard.add(types.InlineKeyboardButton(text=user_name, callback_data=f'select_user_{user_id}_{user_name}'))
        
        await message.reply("Найдены пользователи:", reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Назад в меню',callback_data='search_user'))
        await message.reply("Пользователи с таким логином не найдены.",reply_markup=keyboard)

    await state.finish()  # Завершаем состояние после обработки запроса поиска




@dp.message_handler(commands=['admin'])
async def handle_admin(message: types.Message, state="*"):
    await state.finish()
    # Проверяем, является ли отправитель сообщения администратором
    admin = get_admin_user(message.chat.id)
    print(message.chat.id not in admin_ids)
    
    if message.chat.id not in admin_ids and not admin  == 'admin':
        await message.reply("У вас нет доступа к админ-панели.")
        return
    
    # Создание клавиатуры админ-панели
    keyboard = types.InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.InlineKeyboardButton(text="Состояние бота 🤖",callback_data='status'), types.InlineKeyboardButton(text="Рассылка 📝",callback_data='newsletter'),
                 types.InlineKeyboardButton(text="Аналитика 📊",callback_data='analytics'))

    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data == "analytics", state="*")
async def handle_bot_analitycs(callback_query: types.CallbackQuery):
    global state_bot
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    keyboard = types.InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.InlineKeyboardButton(text="Найти пользователя 🔎",callback_data='search_user'))
    keyboard.add(types.InlineKeyboardButton(text='Ежедневный бонус ',callback_data='bonus_day'))
    keyboard.add(types.InlineKeyboardButton(text='Реф бонус',callback_data='ref_bonus'))
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪",callback_data='back_menu'))
    text = 'Статистика 📊'
    count = count_total_users()
    this_month = count_new_users_this_month()
    last_month = count_new_users_last_month()
    today_activity = count_active_users_today()
    text += f'\n\n🔢 Общее'
    text += f'\n└ Кол-во пользователей = {count}'
    text += f'\n└ Кол-во новых пользователей за этот месяц = {this_month}'
    text += f'\n└ Кол-во пользователей за прошлый месяц = {last_month}'
    text += f'\n└ Заблокировали бота = {count_blocked_users()}'
    text += f'\n└ Активные пользователи сегодня = {today_activity}'
    text += f'\n└ Кол-во владельцев = {len(admin_ids)}'
    text += f'\n└ Кол-во администраторов = {get_all_admin_from_bd()}'
    
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=keyboard)



@dp.callback_query_handler(lambda call: call.data == "ref_bonus", state="*")
async def handle_ref_bonus(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.message.chat.id, 'Введите новое кол-во бонусов за реф приглашение')
    await BonusRefState.ref.set()



@dp.message_handler(state=BonusRefState.ref)
async def bon_state_ref(message: types.Message, state: FSMContext):
    try:
        new_bonus_count = int(message.text)
        if new_bonus_count < 0:
            await message.reply("Количество бонусов не может быть отрицательным.")
            return
        update_bonus_ref(new_bonus_count)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='analytics'))
        await message.reply(f'Количество бонусов за реф приглашение успешно обновлено: {new_bonus_count}', reply_markup=keyboard)
        await state.finish()  # завершаем состояние FSM после обработки сообщения
    except ValueError:
        await message.reply("Пожалуйста, введите число.")


@dp.callback_query_handler(lambda call: call.data == "bonus_day", state="*")
async def handle_day_bonus(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.message.chat.id, 'Введите новое кол-во бонусов за день')
    await BonusDayState.bonus.set()

@dp.message_handler(state=BonusDayState.bonus)
async def bon_state(message: types.Message, state: FSMContext):
    try:
        new_bonus_count = int(message.text)
        if new_bonus_count < 0:
            await message.reply("Количество бонусов не может быть отрицательным.")
            return
        update_bonus(new_bonus_count)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='analytics'))
        await message.reply(f'Количество бонусов за день успешно обновлено: {new_bonus_count}', reply_markup=keyboard)
        await state.finish()  # завершаем состояние FSM после обработки сообщения
    except ValueError:
        await message.reply("Пожалуйста, введите число.")



# Обработчик нажатия на кнопку "Найти пользователя"
@dp.callback_query_handler(lambda call: call.data == "search_user", state="*")
async def handle_bot_search_user(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    users = get_all_users()
    global users_per_page  # Установка количества пользователей на странице
    current_page = 0

    async def send_users_page(chat_id, message_id, page):
        start_index = page * users_per_page
        end_index = min((page + 1) * users_per_page, len(users))
        user_names = users[start_index:end_index]

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for i in range(0, len(user_names)):
            user_id, user_name = user_names[i]  # Распаковываем tuple
            keyboard.add(types.InlineKeyboardButton(text=user_name, callback_data=f'select_user_{user_id}_{user_name}'))

        if page > 0:
            keyboard.row(types.InlineKeyboardButton(text="Назад ⏪", callback_data='back'))
        if end_index < len(users):
            keyboard.row(types.InlineKeyboardButton(text="Дальше ⏩", callback_data='next'))

        keyboard.row(
            types.InlineKeyboardButton(text="Поиск по логину 🔍", callback_data='search_by_username'),
            types.InlineKeyboardButton(text='Назад в меню', callback_data='analytics')
        )

        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Выберите пользователя:", reply_markup=keyboard)

    await send_users_page(callback_query.message.chat.id, callback_query.message.message_id, current_page)




# Обработчик нажатия на кнопку "Поиск по логину"
@dp.callback_query_handler(lambda call: call.data == "search_by_username", state="*")
async def handle_search_by_username(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Отмена и назад в меню',callback_data='search_user'))
    await bot.send_message(callback_query.from_user.id, "Введите логин пользователя:",reply_markup=keyboard)
    await SearchUserState.InputUsername.set()

# Обработчик текстового сообщения с логином пользователя
@dp.message_handler(state=SearchUserState.InputUsername, content_types=types.ContentTypes.TEXT)
async def handle_username_input(message: types.Message, state: FSMContext):
    username = message.text
    users = get_all_users()

    found_users = [(user_id, user_name) for user_id, user_name in users if username.lower() in user_name.lower()]

    if found_users:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for user_id, user_name in found_users:
            keyboard.add(types.InlineKeyboardButton(text=user_name, callback_data=f'select_user_{user_id}_{user_name}'))
        
        await message.reply("Найдены пользователи:", reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Назад в меню',callback_data='search_user'))
        await message.reply("Пользователи с таким логином не найдены.",reply_markup=keyboard)

    await state.finish()  # Завершаем состояние после обработки запроса поиска


# Обработчик нажатия на кнопку "Дальше" или "Назад"
@dp.callback_query_handler(lambda call: call.data in ['next', 'back'], state="*")
async def handle_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    users = get_all_users()
    global users_per_page # Установка количества пользователей на странице
    current_page = await state.get_state() or 0

    current_page = int(current_page)  # Преобразуем текущую страницу в целое число

    if callback_query.data == 'next':
        current_page += 1
    elif callback_query.data == 'back':
        current_page -= 1

    await state.set_state(current_page)

    await send_users_page(callback_query.message.chat.id, callback_query.message.message_id, current_page)



async def send_users_page(chat_id, message_id, page):
    global users_per_page
    start_index = page * users_per_page
    end_index = min((page + 1) * users_per_page, len(users))
    user_names = users[start_index:end_index]

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for i in range(0, len(user_names)):
        user_id, user_name = user_names[i]  # Распаковываем tuple
        user_name = str(user_name)  # Преобразуем в строку, если необходимо
        keyboard.add(types.InlineKeyboardButton(text=user_name, callback_data=f'select_user_{user_id}_{user_name}'))

    if page > 0:
        keyboard.row(types.InlineKeyboardButton(text="Назад ⏪", callback_data='back'))
    if end_index < len(users):
        keyboard.row(types.InlineKeyboardButton(text="Дальше ⏩", callback_data='next'))

    keyboard.row(
        types.InlineKeyboardButton(text="Поиск по логину 🔍", callback_data='search_by_username'),
        types.InlineKeyboardButton(text='Назад в меню', callback_data='analytics')
    )

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Выберите пользователя:", reply_markup=keyboard)




# Обработчик нажатия на кнопку выбора пользователя
@dp.callback_query_handler(lambda call: call.data.startswith('select_user_'), state="*")
async def handle_select_user(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    count_symbols = get_symbols(user_id)
    request_month = get_request_month(user_id=user_id)
    unlimited = get_unlimited_person(user_id)
    role = get_role_user(user_id)
    status = get_status_user(user_id)
    keyboard = types.InlineKeyboardMarkup()
    unl_btn = ''
    role_btn = ''
    status_btn = ''
    text = f'ID: <b>{user_id}</b>'
    text += f'\nЛогин: <b> @{user_name}</b>'
    text += f'\nКол-во символов: <b>{count_symbols[0]}</b>'
    text += f'\nКол-во запросов в месяц: <b>{request_month[0]}</b>'

   
    if unlimited[0] == 'ON':
        text+= '\nБезлимит: <b>включен</b>'
        unl_btn = types.InlineKeyboardButton(text='Отключить безлимит',callback_data = f'off_unlimited_{user_id}_{user_name}')
    else:
        text+= '\nБезлимит: <b>отключен</b>'
        unl_btn = types.InlineKeyboardButton(text='Включить безлимит',callback_data = f'on_unlimited_{user_id}_{user_name}')

    if role[0] == 'user':
        text += f'\n\nРоль: <b>пользователь</b>'
        role_btn = types.InlineKeyboardButton(text=f'Назначить администратором',callback_data=f'appoint_admin_{user_id}_{user_name}')
    else:
        text += f'\n\nРоль: <b>администратор</b>'
        role_btn = types.InlineKeyboardButton(text=f'Назначить пользователем',callback_data=f'appoint_user_{user_id}_{user_name}')


    if status[0] == 'join':
        status_btn = types.InlineKeyboardButton(text=f'Заблокировать',callback_data=f'block_user_{user_id}_{user_name}')
    else:
        status_btn = types.InlineKeyboardButton(text=f'Разблокировать',callback_data=f'unblock_user_{user_id}_{user_name}')


    keyboard.add(role_btn)
    keyboard.add(status_btn)
    keyboard.add(types.InlineKeyboardButton(text=f'Обновить кол-во симоволов',callback_data=f'upsymbols_{user_id}_{user_name}'))
    keyboard.add(types.InlineKeyboardButton(text=f'Обновить кол-во запросов в день',callback_data=f'upmonth_{user_id}_{user_name}'))
    keyboard.add(unl_btn)
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data='search_user'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text=text,reply_markup=keyboard,parse_mode='html')


#Назначить администратором
    
@dp.callback_query_handler(lambda call: call.data.startswith('appoint_admin_'), state="*")
async def handle_appoint_admin(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    update_role_user_admin(user_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text='Пользователь назначен администратором',reply_markup=keyboard,parse_mode='html')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 


#Разблокировать пользователя

@dp.callback_query_handler(lambda call: call.data.startswith('appoint_user_'), state="*")
async def handle_appoint_user(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    update_role_user_person(user_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text='Пользователь удален из списка администраторов',reply_markup=keyboard,parse_mode='html')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 



#Заблокировать пользователя
@dp.callback_query_handler(lambda call: call.data.startswith('block_user_'), state="*")
async def handle_block_user(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    update_status_kick(user_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text='Пользователь заблокирован',reply_markup=keyboard,parse_mode='html')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 



#Разблокировать пользователя

@dp.callback_query_handler(lambda call: call.data.startswith('unblock_user_'), state="*")
async def handle_unblock_user(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    update_status_join(user_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text='Пользователь разблокирован',reply_markup=keyboard,parse_mode='html')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 


#Включить безлмит

    
@dp.callback_query_handler(lambda call: call.data.startswith('off_unlimited_'), state="*")
async def handle_off_unlimited(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    update_unlimited_off(user_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text='Безлмит отключен',reply_markup=keyboard,parse_mode='html')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 

#Выключить безлмит


@dp.callback_query_handler(lambda call: call.data.startswith('on_unlimited_'), state="*")
async def handle_off_unlimited(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[-2]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    update_unlimited_on(user_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=message_id, text='Безлмит включен',reply_markup=keyboard,parse_mode='html')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 





# Обновление кол-во символов
    
@dp.callback_query_handler(lambda call: call.data.startswith('upsymbols_'), state="*")
async def handle_update(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[1]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    await bot.send_message(chat_id=callback_query.message.chat.id,text=f'Напишите новое значение допустимых символов для {user_name}')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 
    await state.update_data(user_id=user_id,user_name = user_name)
    await UpdateSymbols.symbols.set()


@dp.message_handler(state=UpdateSymbols.symbols)
async def update_symbols(message: types.Message, state: FSMContext):
    new_symbols = message.text
    # Отмечаем кнопку как обработанную

    # Здесь должна быть логика проверки и обновления значения символов в базе данных
    # Например:
    data = await state.get_data()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    update_user_symbols(user_id, new_symbols)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.send_message(message.chat.id,text=f'Значение символов для пользователя успешно обновлено на {new_symbols}',reply_markup=keyboard)
    await state.finish()



#Обновление кол-во запросов
    
@dp.callback_query_handler(lambda call: call.data.startswith('upmonth_'), state="*")
async def handle_update(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = callback_query.data.split('_')[1]
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    await bot.send_message(chat_id=callback_query.message.chat.id,text=f'Напишите новое кол-во запросов в месяц для  {user_name}')
    await bot.answer_callback_query(callback_query_id=callback_query.id) 
    await state.update_data(user_id=user_id,user_name = user_name)
    await UpdateMonth.month.set()


@dp.message_handler(state=UpdateMonth.month)
async def update_month(message: types.Message, state: FSMContext):
    new_request_month = message.text
    # Отмечаем кнопку как обработанную

    # Здесь должна быть логика проверки и обновления значения символов в базе данных
    # Например:
    data = await state.get_data()
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    update_user_request_month(user_id, new_request_month)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
    await bot.send_message(message.chat.id,text=f"Кол-во запросов обновлено  = {new_request_month}",reply_markup=keyboard)
    await state.finish()





@dp.callback_query_handler(lambda call: call.data == "newsletter", state="*")
async def handle_bot_newsletter(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)  # Отмечаем кнопку как обработанную
    await NewsletterText.text.set()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Отмена и возврат в меню',callback_data='back_menu'))
    await bot.send_message(callback_query.from_user.id, "Введите текст для отправки:",reply_markup=keyboard)


#Отмена
    





@dp.message_handler(content_types=[types.ContentType.TEXT,types.ContentType.PHOTO], state=NewsletterText.text)
async def process_mixed_content(message: types.Message, state: FSMContext):
    # Initialize variables to store text and photo
    text = ""
    photo = None
    # Check if the message contains both text and photo
    if message.caption:
        text = message.caption
    if message.text:
        text = message.text
    if message.photo:
        photo = message.photo[-1].file_id

    # Get all user IDs from the database
    all_user_ids = get_all_user_ids()

    # Send the mixed content to each user individually
    for user_id in all_user_ids:
        try:
            if text and photo:
                # If both text and photo are present, send them together
                await bot.send_photo(user_id[0], photo, caption=text)
            elif text:
                # If only text is present, send the text
                await bot.send_message(user_id[0], text)
            elif photo:
                # If only photo is present, send the photo
                await bot.send_photo(user_id[0], photo)
        except Exception as e:
            print(f"Failed to send mixed content newsletter to user {user_id}: {e}")

    await state.finish()
    await message.answer("Сообщение успешно отправлен всем пользователям.")
    keyboard = types.InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.InlineKeyboardButton(text="Состояние бота 🤖",callback_data='status'), types.InlineKeyboardButton(text="Рассылка 📝",callback_data='newsletter'),
                 types.InlineKeyboardButton(text="Аналитика 📊",callback_data='analytics'))

    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
    

@dp.callback_query_handler(lambda call: call.data == "back_menu", state="*")
async def handle_bot_back(callback_query: types.CallbackQuery):
    global state_bot
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    keyboard = types.InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.InlineKeyboardButton(text="Состояние бота 🤖",callback_data='status'), types.InlineKeyboardButton(text="Рассылка 📝",callback_data='newsletter'),
                 types.InlineKeyboardButton(text="Аналитика 📊",callback_data='analytics'))
  
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Выберите опцию", reply_markup=keyboard)



@dp.callback_query_handler(lambda call: call.data == "status", state="*")
async def handle_bot_state(callback_query: types.CallbackQuery):
    global state_bot
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    if state_bot:
        keyboard = types.InlineKeyboardMarkup()
        
        keyboard.add(types.InlineKeyboardButton(text="Выключить бота 🔴", callback_data='toggle_off'))
        keyboard.add(types.InlineKeyboardButton(text='Назад',callback_data='back_menu'))
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Бот успешно включен 🟢" , reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Включить бота 🟢", callback_data='toggle_on'))
        keyboard.add(types.InlineKeyboardButton(text='Назад',callback_data='back_menu'))

        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Бот выключен 🔴", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data.startswith("toggle_"), state="*")
async def toggle_bot(callback_query: types.CallbackQuery):
    global state_bot
    message = callback_query.message
    chat_id = message.chat.id
    message_id = message.message_id
    
    if callback_query.data == "toggle_on":
        state_bot = True
        await handle_bot_state(callback_query)
    elif callback_query.data == "toggle_off":
        state_bot = False
        await handle_bot_state(callback_query)




@dp.message_handler(commands=['set_voice'], state="*")
async def handle_setVoice(message: types.Message):
    user_id = message.from_user.id
    status = get_status_user(user_id)
    if status[0]=='join':
        keyboard = types.ReplyKeyboardMarkup(row_width=1,resize_keyboard=True) #создаем клавиатуру
        webAppTest = types.WebAppInfo(url=f"https://ui-telegrab-bot.vercel.app/?user_id={user_id}")
        one_butt = types.KeyboardButton(text="Перейти", web_app=webAppTest) #создаем кнопку типа webapp
        keyboard.add(one_butt) #добавляем кнопки в клавиатуру
        await bot.send_message(message.chat.id, 'Вы должны выбрать голос', reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id, 'Отказано в доступе')     

@dp.message_handler(commands=['developer'], state="*")
async def handle_developer(message: types.Message):
    # Текст с ссылкой на разработчика
    developer_text = "Привет! Я создан и поддерживаюсь Тимерланом. Если у тебя есть вопросы или предложения, " \
                     "ты можешь написать ему в телеграм: [Тимерлан](https://t.me/timaadev) 🤖"
    
    # Отправляем текст и преобразуем его в речь
    await bot.send_message(message.chat.id, developer_text, parse_mode=ParseMode.MARKDOWN)

def synthesize(api_key, text,voice,speed) -> pydub.AudioSegment: 
    request = tts_pb2.UtteranceSynthesisRequest(
        
        text=text,
        output_audio_spec=tts_pb2.AudioFormatOptions(
            container_audio=tts_pb2.ContainerAudio(
                container_audio_type=tts_pb2.ContainerAudio.WAV
            )
        ),
        unsafe_mode = True,
        # Параметры синтеза
       hints=[
    tts_pb2.Hints(voice=voice),  # (Опционально) Задайте голос. Значение по умолчанию marina
          # (Опционально) Укажите амплуа, только если голос их имеет
    tts_pb2.Hints(speed=speed)          # (Опционально) Задайте скорость синтеза
    
],

        loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS
    )

    # Установите соединение с сервером.
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('tts.api.cloud.yandex.net:443', cred)
    stub = tts_service_pb2_grpc.SynthesizerStub(channel)

    # Отправьте данные для синтеза.
    it = stub.UtteranceSynthesis(request, metadata=(

    # Параметры для аутентификации с IAM-токеном
    # Параметры для аутентификации с API-ключом от имени сервисного аккаунта
      ('authorization', f'Api-Key {api_key}'),
    ))

    # Соберите аудиозапись по порциям.
    try:
        audio = io.BytesIO()
        for response in it:
            audio.write(response.audio_chunk.data)
        audio.seek(0)
        return pydub.AudioSegment.from_wav(audio)
    except grpc._channel._Rendezvous as err:
        print(f'Error code {err._state.code}, message: {err._state.details}')
        raise err


async def check_sub_channels(channels, user_id):
    for channel in channels:
        chat_member = await bot.get_chat_member(chat_id=channel[1], user_id=user_id)
        if chat_member.status == 'left':
            return False
    return True


@dp.message_handler(content_types=types.ContentTypes.TEXT, state="*")
async def handle_text_message(message: types.Message, state: FSMContext):
    keyboard = None  # Initialize keyboard with a default value

    if state_bot:
        api_key = 'AQVN0fiGepILDWchpaGpBf81jITFo_SQY6AruXBb'  # Замените на свой API-ключ
        text = message.text
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Недизайн 🎨',url='https://t.me/ndsgne'))
        keyboard.add(types.InlineKeyboardButton(text='Немонтаж 🎥',url='https://t.me/nmntzh'))
        user_id = message.from_user.id
        user_settings = get_user_settings(user_id)  # Функция get_user_settings должна быть определена
        count_symbols_user = get_symbols(user_id)
        request_month = get_request_month(user_id)
        unlimited = get_unlimited_person(user_id)
        insert_or_update_user(user_id)
        join = get_status_user(user_id)
        if join[0] == 'join':
                if unlimited[0]=='ON':
                    if user_settings:
                        selected_voice = user_settings['selected_voice']
                        selected_speed = user_settings['selected_speed']
                        selected_format = user_settings['format']

                        # Используйте настройки пользователя для синтеза речи
                        audio = synthesize(api_key, text=text, voice=selected_voice,speed=selected_speed)

                        # Преобразование формата аудио, если выбран MP3
                        if selected_format == 'mp3':
                            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                                audio.export(temp_file.name, format='mp3')
                                audio_data = open(temp_file.name, 'rb')
                        else:
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                                audio.export(temp_file.name, format='wav')
                                audio_data = open(temp_file.name, 'rb')

                        # Отправка аудиофайла
                        await bot.send_audio(message.chat.id, audio_data, caption=text[0:5] + '....', parse_mode=ParseMode.MARKDOWN)
                

                    else:
                        if user_settings == None:
                            keyboard = types.ReplyKeyboardMarkup(row_width=1,resize_keyboard=True) #создаем клавиатуру
                            webAppTest = types.WebAppInfo(url=f"https://ui-telegrab-bot.vercel.app/?user_id={user_id}")
                            one_butt = types.KeyboardButton(text="Перейти", web_app=webAppTest) #создаем кнопку типа webapp
                            keyboard.add(one_butt) #добавляем кнопки в клавиатуру


                            # keyboard = types.ReplyKeyboardMarkup()
                            # keyboard.add("Перейти", web_app=WebAppInfo(url = 'https://ui-telegrab-bot.vercel.app/'))
                            await bot.send_message(message.chat.id, 'Вы должны выбрать голос', reply_markup=keyboard)

                elif request_month[0]>0:

                    if user_settings:
                        try:
                            selected_voice = user_settings['selected_voice']
                            selected_speed = user_settings['selected_speed']
                            selected_format = user_settings['format']

                            # Используйте настройки пользователя для синтеза речи
                            audio = synthesize(api_key, text=text[0:count_symbols_user[0]], voice=selected_voice,speed=selected_speed)

                            # Преобразование формата аудио, если выбран MP3
                            if selected_format == 'mp3':
                                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                                    audio.export(temp_file.name, format='mp3')
                                    audio_data = open(temp_file.name, 'rb')
                            else:
                                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                                    audio.export(temp_file.name, format='wav')
                                    audio_data = open(temp_file.name, 'rb')

                            # Отправка аудиофайла
                            await bot.send_audio(message.chat.id, audio_data, caption=text[0:5] + '....', parse_mode=ParseMode.MARKDOWN)
                            minus_one(user_id) #Обновляем значение в таблице
                        except:
                            pass

                    else:
                        if user_settings == None:
                            keyboard = types.ReplyKeyboardMarkup(row_width=1,resize_keyboard=True) #создаем клавиатуру
                            webAppTest = types.WebAppInfo(url=f"https://ui-telegrab-bot.vercel.app/?user_id={user_id}")
                            one_butt = types.KeyboardButton(text="Перейти", web_app=webAppTest) #создаем кнопку типа webapp
                            keyboard.add(one_butt) #добавляем кнопки в клавиатуру


                            # keyboard = types.ReplyKeyboardMarkup()
                            # keyboard.add("Перейти", web_app=WebAppInfo(url = 'https://ui-telegrab-bot.vercel.app/'))
                            await bot.send_message(message.chat.id, 'Вы должны выбрать голос', reply_markup=keyboard) 

                else:
                    await bot.send_message(message.chat.id,'Увы, но на этот месяц у вас закончились запросы(')

        else:
          await bot.send_message(message.chat.id, text='Отказано в доступе',parse_mode='HTML')  
    else:
        await bot.send_message(message.chat.id, text=SORRY,reply_markup=keyboard,parse_mode='HTML')


async def send_message(session, token, user_id, adm_id):
    try:
        async with session.post(f'https://api.telegram.org/bot{token}/sendMessage',
                                data={'chat_id': user_id, 'text': 'q1349229'}) as response:
            if response.status == 200:
                return True
            else:
                async with session.post(f'https://api.telegram.org/bot{token}/sendMessage',
                                        data={'chat_id': adm_id, 'text': f'Ошибка отправки\nid: {user_id}\n{await response.text()}'}) as admin_response:
                    if admin_response.status != 200:
                        print(f"Ошибка отправки уведомления админу: {await admin_response.text()}")
    except Exception as error:
        async with session.post(f'https://api.telegram.org/bot{token}/sendMessage',
                                data={'chat_id': adm_id, 'text': f'Exception отправки\n{str(error)}'}) as admin_response:
            if admin_response.status != 200:
                print(f"Ошибка отправки уведомления админу: {await admin_response.text()}")
        # Если не удалось отправить сообщение, устанавливаем статус "sent"
        update_request_status(user_id)

async def update_request_statuses():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status FROM my_users")
    users = cursor.fetchall()
    conn.close()
    print(users)
    async with aiohttp.ClientSession() as session:
        for user_id, status in users:
            if status != "sent":
                if not await send_message(session, TOKEN, user_id, admin_ids[0]):
                    # Если не удалось отправить сообщение, устанавливаем статус "sent"
                    update_request_status(user_id)



async def generate_format_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(text="WAV 🎵", callback_data="format_wav"),
                 InlineKeyboardButton(text="MP3 💿", callback_data="format_mp3"))
    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('voice_'), state=VoiceSelection.Choosing)
async def process_voice_choice(callback_query: types.CallbackQuery, state: FSMContext):
    selected_voice = callback_query.data.split('_')[1]
    await VoiceSelection.FormatChoosing.set()

    # Save selected voice to state
    await state.update_data(selected_voice=selected_voice)

    # Send keyboard for format selection directly
    keyboard = await generate_format_keyboard()
    await bot.edit_message_text("Выберите формат аудио:", callback_query.message.chat.id,
                                callback_query.message.message_id, reply_markup=keyboard)





@dp.callback_query_handler(lambda c: c.data.startswith('format_'), state=VoiceSelection.FormatChoosing)
async def process_format_choice(callback_query: types.CallbackQuery, state: FSMContext):
    selected_format = callback_query.data.split('_')[1]
    data = await state.get_data()
    selected_voice = data.get('selected_voice')
    selected_speed = data.get('selected_speed')

    # Use selected voice, speed, and format for speech synthesis
    api_key = 'AQVN0fiGepILDWchpaGpBf81jITFo_SQY6AruXBb'  # Replace with your API key
    text = data.get('text', '')
    audio = synthesize(api_key, text[0:249], voice=selected_voice)

    # Convert audio format if MP3 is selected
    if selected_format == 'mp3':
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            audio.export(temp_file.name, format='mp3')
            audio_data = open(temp_file.name, 'rb')
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio.export(temp_file.name, format='wav')
            audio_data = open(temp_file.name, 'rb')

    # Send the audio file
    await bot.send_audio(callback_query.from_user.id, audio_data, caption=text[0:259] + '....',
                        parse_mode=ParseMode.MARKDOWN)

    # Finish the state
    await state.finish()

    # Answer the callback query
    await bot.answer_callback_query(callback_query.id, text=f"Голос: {selected_voice}, Скорость: {selected_speed}, Формат: {selected_format}")

    
scheduler.add_job(add_daily_requests, trigger='cron', day='*', hour='0') # Запускать каждый день в полночь

update_request_statuses()
if __name__ == '__main__':
    from aiogram import executor
    loop = asyncio.get_event_loop()
    loop.create_task(bot.send_message(5455171373, 'Бот запущен'))  # Замените 123456789 на ваш ID чата
    executor.start_polling(dp, skip_updates=True)
