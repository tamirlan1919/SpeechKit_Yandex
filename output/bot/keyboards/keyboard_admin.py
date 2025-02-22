from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_admin_keyboard() -> InlineKeyboardMarkup:
    """Создание клавиатуры при /admin"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Состояние бота 🤖", callback_data='status')],
        [InlineKeyboardButton(text="Рассылка 📝", callback_data='newsletter')],
        [InlineKeyboardButton(text="Аналитика 📊", callback_data='analytics')]
    ])
    return keyboard


def analytic_keyboard() -> InlineKeyboardMarkup:
    """Клавиатуры аналитики"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Найти пользователя 🔎", callback_data='search_user')],
        [InlineKeyboardButton(text='Ежедневный бонус', callback_data='bonus_day')],
        [InlineKeyboardButton(text='Кол-во символов', callback_data='count_symbols')],
        [InlineKeyboardButton(text='Реф бонус', callback_data='ref_bonus')],
        [InlineKeyboardButton(text="Назад ⏪", callback_data='back_menu')]
    ])
    return keyboard


def back_to_analytic_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='analytics')]
    ])
    return keyboard


def login_search_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Отмена и назад в меню', callback_data='search_user')]
    ])
    return keyboard
