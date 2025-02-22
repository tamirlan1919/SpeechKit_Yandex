from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from output.bot.database.db import AsyncSessionLocal
from output.bot.database.repository import *
from output.bot.config import admin_ids
from output.bot.keyboards.keyboard_admin import main_admin_keyboard, analytic_keyboard, back_to_analytic_keyboard, \
    login_search_keyboard
from output.bot.states.state import BonusRefState, CountSymbolsState, BonusDayState, SearchUserState, UpdateSymbols, \
    UpdateMonth, NewsletterText
from output.bot.config import state_bot, users_per_page

router = Router()


@router.message(Command("admin"))
async def handle_admin(message: types.Message, state: FSMContext):
    """Обработчик команды /admin"""
    async with AsyncSessionLocal() as db:
        await state.clear()  # Очищаем текущее состояние

        # Проверяем, является ли отправитель сообщения администратором
        admin = await get_admin_user(message.chat.id, db)

        if message.chat.id not in admin_ids and admin != 'admin':
            await message.reply("У вас нет доступа к админ-панели.")
            return

        await message.answer("Выберите действие:", reply_markup=main_admin_keyboard())


@router.callback_query(F.data == "analytics")
async def handle_bot_analytics(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки "Аналитика"""
    async with AsyncSessionLocal() as db:
        text = 'Статистика 📊'
        count = await count_total_users(db)
        this_month = await count_new_users_this_month(db)
        last_month = await count_new_users_last_month(db)
        today_activity = await count_active_users_today(db)
        block_bot = await count_blocked_users(db)
        count_admins = await get_all_admin_from_bd(db)

        text += f'\n\n🔢 Общее'
        text += f'\n└ Кол-во пользователей = {count}'
        text += f'\n└ Кол-во новых пользователей за этот месяц = {this_month}'
        text += f'\n└ Кол-во пользователей за прошлый месяц = {last_month}'
        text += f'\n└ Заблокировали бота = {block_bot}'
        text += f'\n└ Активные пользователи сегодня = {today_activity}'
        text += f'\n└ Кол-во владельцев = {len(admin_ids)}'
        text += f'\n└ Кол-во администраторов = {count_admins}'

        # Редактирование сообщения с обновленной статистикой
        await callback_query.message.edit_text(text, reply_markup=analytic_keyboard())


@router.callback_query(F.data == "ref_bonus")
async def handle_ref_bonus(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки "Реф бонус"""
    await callback_query.answer()
    await callback_query.message.answer('Введите новое кол-во бонусов за реф приглашение')
    await state.set_state(BonusRefState.ref)  # Переход в состояние ref_bonus_state


@router.message(BonusRefState.ref)
async def bon_state_ref(message: types.Message, state: FSMContext):
    """Обработчик состояния Реф бонуса"""
    async with AsyncSessionLocal() as db:
        try:
            new_bonus_count = int(message.text)
            if new_bonus_count < 0:
                await message.reply("Количество бонусов не может быть отрицательным.")
                return
            await update_bonus_ref(new_bonus_count, db)

            await message.reply(f'Количество бонусов за реф приглашение успешно обновлено: {new_bonus_count}',
                                reply_markup=back_to_analytic_keyboard())
            await state.clear()  # Завершение состояния после обработки сообщения
        except ValueError:
            await message.reply("Пожалуйста, введите число.")


@router.callback_query(F.data == "count_symbols")
async def handle_count_symbols(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки кол-во символов """
    await callback_query.answer()
    await callback_query.message.answer('Введите новое кол-во символов за запрос')
    await state.set_state(CountSymbolsState.count)  # Установка состояния для обработки ввода количества символов


@router.message(CountSymbolsState.count)
async def count_symbols_state(message: types.Message, state: FSMContext):
    """Обработчик состояния кол-во символов"""
    async with AsyncSessionLocal() as db:
        try:
            new_count = int(message.text)
            if new_count < 0:
                await message.reply("Количество символов не может быть отрицательным.")
                return
            await update_count_symbol(new_count, db)
            await message.reply(f'Количество символов за запрос успешно обновлено: {new_count}',
                                reply_markup=back_to_analytic_keyboard())
            await state.clear()  # Завершение состояния FSM
        except ValueError:
            await message.reply("Пожалуйста, введите число.")


@router.callback_query(F.data == "bonus_day")
async def handle_day_bonus(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки Ежедневный бонус"""
    await callback_query.answer()
    await callback_query.message.answer('Введите новое кол-во бонусов за день')
    await state.set_state(BonusDayState.bonus)  # Установка состояния для обработки ввода бонусов за день


@router.message(BonusDayState.bonus)
async def bon_state(message: types.Message, state: FSMContext):
    """Обработчик состояния дневного бонуса"""
    async with AsyncSessionLocal() as db:
        try:
            new_bonus_count = int(message.text)
            if new_bonus_count < 0:
                await message.reply("Количество бонусов не может быть отрицательным.")
                return
            await update_bonus(new_bonus_count, db)
            await message.reply(f'Количество бонусов за день успешно обновлено: {new_bonus_count}',
                                reply_markup=back_to_analytic_keyboard())
            await state.clear()  # Завершение состояния FSM
        except ValueError:
            await message.reply("Пожалуйста, введите число.")


async def send_users_page(callback_query: types.CallbackQuery, page: int):
    """Функция для отправки списка пользователей с пагинацией"""
    async with AsyncSessionLocal() as db:
        users = await get_all_users(db)

        if not users:
            await callback_query.message.edit_text("Пользователи не найдены.", reply_markup=None)
            return

        start_index = page * users_per_page
        end_index = min(start_index + users_per_page, len(users))
        user_names = users[start_index:end_index]

        keyboard = InlineKeyboardBuilder()

        for user_id, user_name in user_names:
            keyboard.add(InlineKeyboardButton(text=user_name, callback_data=f'select_user_{user_id}_{user_name}'))

        # Кнопки пагинации
        if page > 0:
            keyboard.row(InlineKeyboardButton(text="⏪ Назад", callback_data=f'page_{page - 1}'))
        if end_index < len(users):
            keyboard.row(InlineKeyboardButton(text="Дальше ⏩", callback_data=f'page_{page + 1}'))

        # Доп. кнопки
        keyboard.row(
            InlineKeyboardButton(text="🔍 Поиск по логину", callback_data='search_by_username'),
            InlineKeyboardButton(text="🏠 Назад в меню", callback_data='analytics')
        )

        await callback_query.message.edit_text("Выберите пользователя:", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "search_user")
async def handle_bot_search_user(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Найти пользователя' """
    await callback_query.answer()
    await send_users_page(callback_query, 0)


@router.callback_query(F.data.startswith("page_"))
async def handle_pagination(callback_query: types.CallbackQuery):
    """Обработчик кнопок 'Дальше' и 'Назад' для переключения страниц"""
    await callback_query.answer()
    page = int(callback_query.data.split("_")[1])
    await send_users_page(callback_query, page)


# Обработчик кнопки "Поиск по логину"
@router.callback_query(lambda call: call.data == "search_by_username")
async def handle_search_by_username(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    await callback_query.message.answer("Введите логин пользователя:", reply_markup=login_search_keyboard())
    await state.set_state(SearchUserState.InputUsername)  # Установка состояния для ввода логина


# Обработчик текстового сообщения с логином пользователя
@router.message(SearchUserState.InputUsername)
async def handle_username_input(message: types.Message, state: FSMContext):
    async with AsyncSessionLocal() as db:
        username = message.text
        users = await get_all_users(db)

        found_users = [(user_id, user_name) for user_id, user_name in users if username.lower() in user_name.lower()]
        print(found_users)
        if found_users:
            keyboard = InlineKeyboardBuilder()
            for user_id, user_name in found_users:
                keyboard.add(InlineKeyboardButton(text=user_name, callback_data=f'select_user_{user_id}_{user_name}'))
                keyboard.adjust(1)
            await message.reply("Найдены пользователи:", reply_markup=keyboard.as_markup())
        else:
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text='Назад в меню', callback_data='search_user'))
            await message.reply("Пользователи с таким логином не найдены.", reply_markup=keyboard.as_markup())

        await state.clear()  # Завершаем состояние после обработки запроса поиска


# Обработчик кнопки выбора пользователя
@router.callback_query(F.data.startswith('select_user_'))
async def handle_select_user(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        await callback_query.answer()

        # Разделение данных колбэка по символу '_'
        data_parts = callback_query.data.split('_')

        # Получение user_id и user_name
        user_id = int(data_parts[2])
        user_name = '_'.join(data_parts[3:])  # Все оставшиеся части объединяются для формирования user_name

        count_symbols = await get_symbols(user_id, db)
        request_month = await get_request_month(user_id=user_id, db=db)
        unlimited = await get_unlimited_person(user_id, db)
        role = await get_role_user(user_id, db)
        status = await get_status_user(user_id, db)

        keyboard = InlineKeyboardBuilder()
        text = f'ID: <b>{user_id}</b>'
        text += f'\nЛогин: <b> @{user_name}</b>'
        text += f'\nКол-во символов: <b>{count_symbols}</b>'
        text += f'\nКол-во запросов в день: <b>{request_month}</b>'

        if unlimited == 'ON':
            text += '\nБезлимит: <b>включен</b>'
            unl_btn = InlineKeyboardButton(text='Отключить безлимит',
                                           callback_data=f'off_unlimited_{user_id}_{user_name}')
        else:
            text += '\nБезлимит: <b>отключен</b>'
            unl_btn = InlineKeyboardButton(text='Включить безлимит',
                                           callback_data=f'on_unlimited_{user_id}_{user_name}')

        if role == 'user':
            text += f'\n\nРоль: <b>пользователь</b>'
            role_btn = InlineKeyboardButton(text=f'Назначить администратором',
                                            callback_data=f'appoint_admin_{user_id}_{user_name}')
        else:
            text += f'\n\nРоль: <b>администратор</b>'
            role_btn = InlineKeyboardButton(text=f'Назначить пользователем',
                                            callback_data=f'appoint_user_{user_id}_{user_name}')

        if status == 'join':
            status_btn = InlineKeyboardButton(text=f'Заблокировать', callback_data=f'block_user_{user_id}_{user_name}')
        else:
            status_btn = InlineKeyboardButton(text=f'Разблокировать',
                                              callback_data=f'unblock_user_{user_id}_{user_name}')

        keyboard.add(role_btn)
        keyboard.add(status_btn)
        keyboard.add(
            InlineKeyboardButton(text=f'Обновить кол-во символов', callback_data=f'upsymbols_{user_id}_{user_name}'))
        keyboard.add(
            InlineKeyboardButton(text=f'Обновить кол-во запросов в день',
                                 callback_data=f'upmonth_{user_id}_{user_name}'))
        keyboard.add(unl_btn)
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data='search_user'))
        keyboard.adjust(1)
        await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode='html')


# Назначить администратором
@router.callback_query(F.data.startswith('appoint_admin_'))
async def handle_appoint_admin(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_name = callback_query.data.split('_')[-1]
        user_id = int(callback_query.data.split('_')[-2])
        await update_role_user_admin(user_id, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await callback_query.message.edit_text('Пользователь назначен администратором',
                                               reply_markup=keyboard.as_markup(),
                                               parse_mode='html')
        await callback_query.answer()


## Разблокировать пользователя
@router.callback_query(F.data.startswith('appoint_user_'))
async def handle_appoint_user(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_name = callback_query.data.split('_')[-1]
        user_id = int(callback_query.data.split('_')[-2])
        await update_role_user_person(user_id, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await callback_query.message.edit_text('Пользователь удален из списка администраторов',
                                               reply_markup=keyboard.as_markup(),
                                               parse_mode='html')
        await callback_query.answer()


# Заблокировать пользователя
@router.callback_query(F.data.startswith('block_user_'))
async def handle_block_user(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_name = callback_query.data.split('_')[-1]
        user_id = int(callback_query.data.split('_')[-2])
        await update_status_kick(user_id, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await callback_query.message.edit_text('Пользователь заблокирован', reply_markup=keyboard.as_markup(),
                                               parse_mode='html')
        await callback_query.answer()


# Разблокировать пользователя
@router.callback_query(F.data.startswith('unblock_user_'))
async def handle_unblock_user(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_name = callback_query.data.split('_')[-1]
        user_id = int(callback_query.data.split('_')[-2])
        await update_status_join(user_id, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await callback_query.message.edit_text('Пользователь разблокирован', reply_markup=keyboard.as_markup(),
                                               parse_mode='html')
        await callback_query.answer()


# Включить безлимит
@router.callback_query(F.data.startswith('off_unlimited_'))
async def handle_off_unlimited(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_name = callback_query.data.split('_')[-1]
        user_id = int(callback_query.data.split('_')[-2])
        await update_unlimited_off(user_id, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await callback_query.message.edit_text('Безлимит отключен', reply_markup=keyboard.as_markup(),
                                               parse_mode='html')
        await callback_query.answer()


# Выключить безлимит
@router.callback_query(F.data.startswith('on_unlimited_'))
async def handle_on_unlimited(callback_query: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_name = callback_query.data.split('_')[-1]
        user_id = int(callback_query.data.split('_')[-2])
        await update_unlimited_on(user_id, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await callback_query.message.edit_text('Безлимит включен', reply_markup=keyboard.as_markup(), parse_mode='html')
        await callback_query.answer()


# Обновление кол-во символов
@router.callback_query(F.data.startswith('upsymbols_'))
async def handle_update(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = int(callback_query.data.split('_')[1])
    await callback_query.message.answer(f'Напишите новое значение допустимых символов для {user_name}')
    await callback_query.answer()
    await state.update_data(user_id=user_id, user_name=user_name)
    await state.set_state(UpdateSymbols.symbols)


# Обновление кол-во символов
@router.message(UpdateSymbols.symbols)
async def update_symbols(message: types.Message, state: FSMContext):
    async with AsyncSessionLocal() as db:
        new_symbols = int(message.text)
        data = await state.get_data()
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        await update_user_symbols(user_id, new_symbols, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await message.answer(f'Значение символов для пользователя успешно обновлено на {new_symbols}',
                             reply_markup=keyboard.as_markup())
        await state.clear()


# Обновление кол-во запросов
@router.callback_query(F.data.startswith('upmonth_'))
async def handle_update_month(callback_query: types.CallbackQuery, state: FSMContext):
    user_name = callback_query.data.split('_')[-1]
    user_id = int(callback_query.data.split('_')[1])
    await callback_query.message.answer(f'Напишите новое кол-во запросов в день для {user_name}')
    await callback_query.answer()
    await state.update_data(user_id=user_id, user_name=user_name)
    await state.set_state(UpdateMonth.month)


@router.message(UpdateMonth.month)
async def update_month(message: types.Message, state: FSMContext):
    async with AsyncSessionLocal() as db:
        new_request_month = message.text
        data = await state.get_data()
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        await update_user_request_month(user_id, new_request_month, db)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Назад ⏪", callback_data=f'select_user_{user_id}_{user_name}'))
        await message.answer(f"Кол-во запросов обновлено  = {new_request_month}", reply_markup=keyboard.as_markup())
        await state.clear()


# Обработчик рассылки
@router.callback_query(F.data == "newsletter")
async def handle_bot_newsletter(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.set_state(NewsletterText.text)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Отмена и возврат в меню', callback_data='back_menu'))
    await callback_query.message.answer("Введите текст для отправки:", reply_markup=keyboard.as_markup())


# Обработчик текста и фото для рассылки
@router.message(NewsletterText.text)
async def process_mixed_content(message: types.Message, state: FSMContext):
    async with AsyncSessionLocal() as db:
        text = message.caption or message.text
        photo = message.photo[-1].file_id if message.photo else None
        await state.clear()

        all_user_ids = await get_all_user_ids(db)

        for user_id in all_user_ids:
            try:
                if text and photo:
                    await message.bot.send_photo(user_id, photo, caption=text)
                elif text:
                    await message.bot.send_message(user_id, text, parse_mode="MarkdownV2",
                                                   disable_web_page_preview=True)
                elif photo:
                    await message.bot.send_photo(user_id, photo)


                elif message.voice:

                    # Получаем file_id голосового сообщения

                    voice_file_id = message.voice.file_id

                    # Отправляем голосовое сообщение пользователю

                    await message.bot.send_voice(chat_id=user_id, voice=voice_file_id)

            except Exception as e:
                print(f"Failed to send mixed content newsletter to user {user_id}: {e}")

        await message.answer("Сообщение успешно отправлен всем пользователям.")
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(text="Состояние бота 🤖", callback_data='status'),
            InlineKeyboardButton(text="Рассылка 📝", callback_data='newsletter'),
            InlineKeyboardButton(text="Аналитика 📊", callback_data='analytics')
        )

        await message.bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard.as_markup())


# Обработчик возврата в меню
@router.callback_query(F.data == "back_menu")
async def handle_bot_back(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.message_id

    await callback_query.message.edit_text("Выберите опцию", reply_markup=main_admin_keyboard())


# Обработчик состояния бота
@router.callback_query(F.data == "status")
async def handle_bot_state(callback_query: types.CallbackQuery):
    if state_bot:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Выключить бота 🔴", callback_data='toggle_off'))
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data='back_menu'))
        await callback_query.message.edit_text("Бот успешно включен 🟢", reply_markup=keyboard.as_markup())
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Включить бота 🟢", callback_data='toggle_on'))
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data='back_menu'))
        await callback_query.message.edit_text("Бот выключен 🔴", reply_markup=keyboard.as_markup())


# Обработчик включения/выключения бота
@router.callback_query(F.data.startswith("toggle_"))
async def toggle_bot(callback_query: types.CallbackQuery):
    global state_bot

    if callback_query.data == "toggle_on":
        state_bot = True
        await handle_bot_state(callback_query)
    elif callback_query.data == "toggle_off":
        state_bot = False
        await handle_bot_state(callback_query)
