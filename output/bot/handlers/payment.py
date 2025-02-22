# Команда /buy
import json
import sqlite3

from output.bot.config import *
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, PreCheckoutQuery, Message, \
    LabeledPrice
from output.bot.database.repository import process_payment, get_symbols_from_subscriptions
from output.bot.database.db import AsyncSessionLocal
from output.bot.keyboards.keyboard_user import get_pay_keyboard

router = Router()


@router.message(Command('buy'))
async def buy_credits(message: Message):
    await message.answer(
        "💳 <b>Пополнение баланса символов</b>\n\n"
        "Выберите подходящий тариф:\n"
        "- <b>20 000 символов</b> — 150 рублей (~15 минут озвучки)\n"
        "- <b>100 000 символов</b> — 600 рублей (~75 минут озвучки)\n"
        "- <b>300 000 символов</b> — 1 500 рублей (~225 минут озвучки)\n\n"
        "🔹 Нажмите на соответствующую кнопку ниже, чтобы выбрать тариф и оплатить.",
        reply_markup=get_pay_keyboard(), parse_mode=ParseMode.HTML
    )


# Обработка нажатий на кнопки тарифов
@router.callback_query(F.data.in_({"20k_symbols", "100k_symbols", "300k_symbols"}))
async def tarif_handler(callback_query: CallbackQuery):
    tariffs = {
        "20k_symbols": {
            "title": "20 000 символов",
            "description": "Вы выбрали тариф 20 000 символов за 150 рублей.После оплаты символы будут добавлены автоматически.",
            "payload": "small_tariff",
            "amount": 100_00  # 150 рублей в копейках
        },
        "100k_symbols": {
            "title": "100 000 символов",
            "description": "Вы выбрали тариф 100 000 символов за 600 рублей.После оплаты символы будут добавлены автоматически.",
            "payload": "middle_tariff",
            "amount": 600_00  # 600 рублей в копейках
        },
        "300k_symbols": {
            "title": "300 000 символов",
            "description": "Вы выбрали тариф 300 000 символов за 1500 рублей.После оплаты символы будут добавлены автоматически.",
            "payload": "large_tariff",
            "amount": 1500_00  # 1 500 рублей в копейках
        }
    }

    tariff = tariffs.get(callback_query.data)
    if not tariff:
        await callback_query.message.answer("Ошибка: тариф не найден.")
        return

    provider_data = {
        "receipt": {
            "items": [
                {
                    "description": tariff["description"],
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{tariff['amount'] / 100:.2f}",  # конвертируем копейки в рубли
                        "currency": "RUB"
                    },
                    "vat_code": "1",  # при необходимости укажите вашу ставку НДС
                    "payment_mode": "full_prepayment",  # режим оплаты
                    "payment_subject": "service"  # признак предмета расчёта
                }
            ],
        }
    }
    await callback_query.answer()
    await callback_query.message.answer_invoice(
        title=tariff["title"],
        description=tariff["description"],
        payload=tariff["payload"],
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=tariff["title"], amount=tariff["amount"])],
        need_email=True,
        need_phone_number=True,
        send_email_to_provider=True,
        send_phone_number_to_provider=True,
        provider_data=json.dumps(provider_data)
    )


# Обработка pre-checkout запроса
@router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)


# Обработка успешного платежа
@router.message(F.successful_payment)
async def successful_payment(message: Message):
    user_id = int(message.from_user.id)
    payload = message.successful_payment.invoice_payload

    tariffs = {
        "small_tariff": {"symbols": 20000, "name": "20 000 символов"},
        "middle_tariff": {"symbols": 100000, "name": "100 000 символов"},
        "large_tariff": {"symbols": 300000, "name": "300 000 символов"}
    }

    tariff = tariffs.get(payload)
    if tariff is None:
        await message.answer("Ошибка: не удалось обработать платёж.")
        return

    total_symbols = tariff["symbols"]
    tariff_name = tariff["name"]

    user_email = message.successful_payment.order_info.email
    user_phone = message.successful_payment.order_info.phone_number

    amount = message.successful_payment.total_amount / 100  # Конвертируем копейки в рубли
    currency = message.successful_payment.currency
    transaction_id = message.successful_payment.provider_payment_charge_id

    # Создаём асинхронную сессию и вызываем process_payment
    async with AsyncSessionLocal() as session:
        await process_payment(
            user_id=user_id,
            total_symbols=total_symbols,
            email=user_email,
            phone=user_phone,
            tariff_name=tariff_name,
            amount=amount,
            currency=currency,
            transaction_id=transaction_id,
            session=session
        )

        user_symbols = await get_symbols_from_subscriptions(user_id, session)

    await message.answer(f'''✅ <b>Оплата успешно завершена!</b>

🔢 <b>Баланс символов: {user_symbols}</b>

🔹 Вы можете начать использовать символы прямо сейчас. Просто отправьте текст, и я озвучу его для вас!

💡 Вы можете проверить свой баланс символов и доступные запросы: /account''', parse_mode=ParseMode.HTML)

