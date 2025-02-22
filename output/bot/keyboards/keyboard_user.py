from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

def startKeyboard() -> InlineKeyboardMarkup:
    """Создание клавиатуры при команде /start"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Прагласительная ссылка 🫂', callback_data='ref_link')]
    ])
    return keyboard


def get_web_keyboard(user_id) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать голос", web_app=WebAppInfo(
                url=f"https://ui-telegrab-bot.vercel.app/?user_id={user_id}"))]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_account_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пополнить баланс', callback_data='deposit_balance')],
        [InlineKeyboardButton(text='Реферальная программа', callback_data='ref_program')],
    ])
    return keyboard


def get_last_request_text_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пополнить баланс', callback_data='buy_command')],
        [InlineKeyboardButton(text='Реферальная программа', callback_data='refs_command')],
    ])
    return keyboard


def to_deposit_balance():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пополнить баланс', callback_data='deposit_balance_without_back')],
    ])
    return keyboard


def to_deposit_balance_from_text():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пополнить баланс', callback_data='deposit_balance_from_text')],
    ])
    return keyboard

def get_pay_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='20k символов — 150р', callback_data='20k_symbols')],
        [InlineKeyboardButton(text='100k символов — 600р', callback_data='100k_symbols')],
        [InlineKeyboardButton(text='300k символов — 1500р', callback_data='300k_symbols')]
    ])
    return keyboard

def get_pay_keyboard_with_back() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='20k символов — 150р', callback_data='20k_symbols')],
        [InlineKeyboardButton(text='100k символов — 600р', callback_data='100k_symbols')],
        [InlineKeyboardButton(text='300k символов — 1500р', callback_data='300k_symbols')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_account')]
    ])
    return keyboard

def get_pay_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='20k символов — 150р', callback_data='20k_symbols')],
        [InlineKeyboardButton(text='100k символов — 600р', callback_data='100k_symbols')],
        [InlineKeyboardButton(text='300k символов — 1500р', callback_data='300k_symbols')],
    ])
    return keyboard

def get_account_keyboard_with_back() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_to_account')]
    ])
    return keyboard
