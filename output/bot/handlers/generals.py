import datetime
from typing import Optional

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, WebAppInfo, KeyboardButton, CallbackQuery
from aiogram.filters import Command
from output.bot.database.db import AsyncSessionLocal
from output.bot.database.repository import (get_status_user, get_request_monthALL, get_count_symbol_all,
                                            add_user, get_invited_users, get_request_mon_for_user, get_bonus_ref,
                                            create_referral_profile,
                                            create_invitation_record, get_symbols_from_subscriptions, get_request_month,
                                            get_bonus_user_ref)
from aiogram.enums.parse_mode import ParseMode
from output.bot.texts import REF_TEXT, welcome_text, balance_symbols, ref_program, balance_symbols_commercial, \
    payment_text
from output.bot.keyboards.keyboard_user import startKeyboard, get_web_keyboard, get_account_keyboard, get_pay_keyboard, \
    get_pay_keyboard_with_back, get_account_keyboard_with_back
from output.bot.texts import help_text

router = Router()


@router.message(Command("developer"))
async def handle_developer(message: Message):
    # Текст с ссылкой на разработчика
    developer_text = (
        "Привет! Я создан и поддерживаюсь Тимерланом. Если у тебя есть вопросы или предложения, "
        "ты можешь написать ему в телеграм: [Тимерлан](https://t.me/timaadev) 🤖"
    )

    # Отправляем текст с использованием Markdown
    await message.answer(developer_text, parse_mode="Markdown")


@router.message(Command("set_voice"))
async def handle_set_voice(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as db:
        user_id = message.from_user.id
        status = await get_status_user(user_id, db)

        if status == 'join':
            await message.answer('Вы должны выбрать голос', reply_markup=get_web_keyboard(message.from_user.id))
        else:
            await message.answer('Отказано в доступе')


@router.message(Command('account'))
async def cmd_account(message: Message):
    async with AsyncSessionLocal() as db:
        symbols = await get_symbols_from_subscriptions(message.from_user.id, db)
        bonus_ref = await get_bonus_user_ref(message.from_user.id, db)

        request_day = await get_request_month(message.from_user.id, db)
        if symbols > 0:
            text = balance_symbols_commercial.format(symbols=symbols, bonus_ref=bonus_ref)
            await message.answer(text, reply_markup=get_account_keyboard(), parse_mode='html')
        else:
            text = balance_symbols.format(symbols=symbols, bonus_ref=bonus_ref, request_day=request_day)
            await message.answer(text, reply_markup=get_account_keyboard(), parse_mode='html')


@router.message(Command('refs'))
async def cmd_refs(message: Message):
    async with AsyncSessionLocal() as db:
        count_ref = await get_bonus_ref(db)
        invited_users_sum = await get_invited_users(user_id=message.from_user.id, session=db) or 0
        dop_requests = await get_bonus_user_ref(message.from_user.id, db)
        print(count_ref)
        print(invited_users_sum)
        print(dop_requests)

    await message.answer(ref_program.format(
        count_ref=str(count_ref) if count_ref else "0",  # Преобразуем в строку
        invited_users_sum=str(invited_users_sum),
        dop_requests=str(dop_requests),
        user_id=message.from_user.id
    ), parse_mode='HTML')


def extract_referral_id(text: str) -> Optional[int]:
    parts = text.split()
    if len(parts) > 1:
        # Предполагаем, что код реферала передаётся в виде "ref123"
        code = parts[-1].lower().replace('ref', '')
        if code.isdigit():
            return int(code)
    return None


@router.message(Command("start"), F.chat.type == "private")
async def handle_start(message: types.Message, state: FSMContext):
    # Clear the state
    await state.clear()

    referal_id = extract_referral_id(message.text)

    # Welcome text

    async with AsyncSessionLocal() as db:
        request_day = await get_request_monthALL(db)
        count_symbol = await get_count_symbol_all(db)

        user_data = {
            "user_id": message.from_user.id,
            "name": message.from_user.username or message.from_user.first_name,
            "subscription_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count_symbol": count_symbol,
            "request_month": request_day,
            "unlimited": 'OFF',
            "status": 'join',
            "role": 'user'
        }

        await add_user(**user_data, db=db)

        # Всегда создаём профиль для нового пользователя,
        # чтобы в будущем можно было учитывать его приглашения.
        await create_referral_profile(message.from_user.id, session=db)
        if referal_id:
            # Создаём запись, связывающую пригласившего и нового пользователя
            await create_invitation_record(referal_id, message.from_user.id, session=db)

        await message.answer(welcome_text, reply_markup=get_web_keyboard(message.from_user.id))


@router.message(Command("start"), ~F.chat.type == "private")
async def handle_start_non_private(message: types.Message, state: FSMContext):
    # Clear the state
    await state.clear()
    await message.answer("Бот работает в личных сообщениях")


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(help_text)


@router.callback_query(F.data == "ref_program")
async def handle_ref_link(callback_query: CallbackQuery):
    async with AsyncSessionLocal() as db:
        count_ref = await get_bonus_ref(db)
        invited_users_sum = await get_invited_users(user_id= callback_query.from_user.id, session=db) or 0
        dop_requests = await get_bonus_user_ref(callback_query.from_user.id, db)
        print(count_ref)
        print(invited_users_sum)
        print(dop_requests)

    await callback_query.message.edit_text(ref_program.format(
        count_ref=str(count_ref) if count_ref else "0",  # Преобразуем в строку
        invited_users_sum=str(invited_users_sum),
        dop_requests=str(dop_requests),
        user_id=callback_query.from_user.id
    ), parse_mode='HTML', reply_markup=get_account_keyboard_with_back())


@router.callback_query(F.data == 'deposit_balance')
async def deposit_balance_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        payment_text,
        reply_markup=get_pay_keyboard_with_back(), parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == 'deposit_balance_from_text')
async def deposit_balance_from_text(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        payment_text,
        reply_markup=get_pay_keyboard_with_back(), parse_mode=ParseMode.HTML
    )




@router.callback_query(F.data.in_(['deposit_balance', 'deposit_balance_without_back']))
async def deposit_balance_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    if callback_query.data == 'deposit_balance':
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=get_pay_keyboard_with_back(), parse_mode=ParseMode.HTML
        )
    else:
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=get_pay_keyboard(), parse_mode=ParseMode.HTML
        )


@router.callback_query(F.data == 'back_to_account')
async def back_to_account_handler(callback_query: CallbackQuery):
    print(callback_query.message.from_user.id)
    async with AsyncSessionLocal() as db:
        symbols = await get_symbols_from_subscriptions(callback_query.from_user.id, db)
        bonus_ref = await get_bonus_user_ref(callback_query.from_user.id, db)
        request_day = await get_request_month(callback_query.from_user.id, db)
        if symbols > 0:
            text = balance_symbols_commercial.format(symbols=symbols, bonus_ref=bonus_ref)
            await callback_query.message.edit_text(text, reply_markup=get_account_keyboard(), parse_mode='html')
        else:
            text = balance_symbols.format(symbols=symbols, bonus_ref=bonus_ref, request_day=request_day)
            await callback_query.message.edit_text(text, reply_markup=get_account_keyboard(), parse_mode='html')
