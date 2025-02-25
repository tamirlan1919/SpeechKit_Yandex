import asyncio

import grpc
import pydub
from aiogram import Router, types, F
from aiogram.types import InputFile
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, BufferedInputFile
from aiogram.fsm.context import FSMContext
import tempfile
import io
from output.bot.config import YANDEX_SPEECH_KEY
from output.bot.database.db import AsyncSessionLocal
from output.bot.database.repository import *
from output.bot.keyboards.keyboard_user import to_deposit_balance, get_account_keyboard, get_last_request_text_keyboard, \
    to_deposit_balance_from_text
from output.bot.texts import over_text, success_voiced, over_text_filter_database, no_commercial_limit_text, \
    success_no_commercial_text, last_request, doLimit
from output.yandex.cloud.ai.tts.v3 import tts_pb2, tts_service_pb2_grpc

router = Router()


@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext):
    text = message.text
    user_id = int(message.from_user.id)
    async with AsyncSessionLocal() as db:

        user_settings = await get_user_settings(user_id, db)
        count_symbols_user = await get_symbols(user_id, db)
        request_month = await get_request_month(user_id, db)
        bonus_user = await get_bonus_user_ref(user_id, db)
        unlimited = await get_unlimited_person(user_id, db)
        subscriptions_symbol = await get_symbols_from_subscriptions(user_id, db)
        join = await get_status_user(user_id, db)

        if join is None:
            await message.answer('Нажмите на /start')
            return

        if join != 'join':
            await message.answer("Отказано в доступе")
            return
            # Обновляем или создаём запись пользователя

        await insert_or_update_user(user_id, db)
        if user_settings:
            selected_voice = user_settings['selected_voice']
            selected_speed = user_settings['selected_speed']
            selected_format = user_settings['format']
            role = user_settings['role']

            if subscriptions_symbol > 0:
                if len(message.text) > 4095:
                    await message.answer(over_text.format(count=subscriptions_symbol))
                    return
                elif len(message.text) > subscriptions_symbol:
                    await message.answer(over_text_filter_database.format(just_count=count_symbols_user,
                                                                          text_count=len(message.text),
                                                                          balance_user=subscriptions_symbol,
                                                                          request_count=request_month))
                else:
                    audio = synthesize(YANDEX_SPEECH_KEY,
                                       text=text,
                                       voice=selected_voice,
                                       speed=selected_speed,
                                       role=role)
                    audio_data = await convert_audio(audio, selected_format)
                    await update_subscriptions_symbols_by_id(message.from_user.id, len(message.text), db)
                    subscriptions_symbol = await get_symbols_from_subscriptions(user_id, db)
                    await message.answer_audio(audio_data,
                                               caption=success_voiced.format(count=subscriptions_symbol))

            elif unlimited == 'ON':
                audio = synthesize(YANDEX_SPEECH_KEY,
                                   text=text,
                                   voice=selected_voice,
                                   speed=selected_speed,
                                   role=role)
                audio_data = await convert_audio(audio, selected_format)
                await message.answer_audio(audio_data, caption=f"{text[:5]}....")

            elif request_month > 0:
                try:
                    max_symbols = await get_count_symbol(user_id, db) or 700
                    audio = synthesize(YANDEX_SPEECH_KEY, text=text[:max_symbols], voice=selected_voice,
                                       speed=selected_speed, role=role)
                    audio_data = await convert_audio(audio, selected_format)
                    if len(text) > max_symbols:
                        await message.answer(
                            no_commercial_limit_text.format(count=max_symbols, length=len(message.text)),
                            reply_markup=to_deposit_balance_from_text())
                    else:

                        if request_month == 1:
                            bonus = await get_bonus_ref(db)
                            await message.answer_audio(
                                audio_data,
                                caption=last_request.format(ref_bonus=bonus, user_id=message.from_user.id),
                                reply_markup=to_deposit_balance_from_text()
                            )
                        elif request_month > 1:
                            await message.answer_audio(
                                audio_data,
                                caption=success_no_commercial_text.format(request_count=request_month,
                                                                          ref_count=bonus_user)
                            )
                        await minus_one(user_id, db)
                except Exception as e:
                    print(f"Error: {e}")

            elif bonus_user > 0:
                try:
                    max_symbols = await get_count_symbol(user_id, db) or 700
                    audio = synthesize(YANDEX_SPEECH_KEY, text=text[:max_symbols], voice=selected_voice,
                                       speed=selected_speed, role=role)
                    audio_data = await convert_audio(audio, selected_format)

                    if len(text) > max_symbols:
                        await message.answer(
                            no_commercial_limit_text.format(count=max_symbols, length=len(message.text)),
                            reply_markup=to_deposit_balance_from_text())
                    else:

                        if bonus_user == 1:
                            bonus = await get_bonus_ref(db)
                            await message.answer_audio(
                                audio_data,
                                caption=last_request.format(ref_bonus=bonus, user_id=message.from_user.id),
                                reply_markup=to_deposit_balance_from_text()
                            )
                        elif bonus_user > 1:
                            await message.answer_audio(
                                audio_data,
                                caption=success_no_commercial_text.format(request_count=request_month,
                                                                          ref_count=bonus_user)
                            )
                        await minus_one_bonus(user_id, db)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                bonus = await get_bonus_ref(db)
                await message.answer(doLimit.format(ref_bonus=bonus, user_id=message.from_user.id),
                                     reply_markup=get_account_keyboard())
        else:
            await send_voice_selection_keyboard(message, user_id)


async def send_voice_selection_keyboard(message: types.Message, user_id: int):

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать голос",
                            web_app=WebAppInfo(url=f"https://ui-telegrab-bot.vercel.app/?user_id={user_id}"))]
        ],
        resize_keyboard=True
    )

    await message.answer("Вы должны выбрать голос", reply_markup=keyboard)


async def convert_audio(audio, selected_format):
    """Конвертирует аудиофайл в нужный формат и возвращает объект BufferedInputFile"""
    with tempfile.NamedTemporaryFile(suffix=f".{selected_format}", delete=True) as temp_file:
        audio.export(temp_file.name, format=selected_format)
        with open(temp_file.name, "rb") as file:
            audio_bytes = file.read()

    return BufferedInputFile(audio_bytes, filename=f"output.{selected_format}")


def synthesize(YANDEX_SPEECH_KEY, text, voice, speed, role='undefined') -> pydub.AudioSegment:
    request = ''
    if role == 'undefined' or role == None:
        request = tts_pb2.UtteranceSynthesisRequest(

            text=text,
            output_audio_spec=tts_pb2.AudioFormatOptions(
                container_audio=tts_pb2.ContainerAudio(
                    container_audio_type=tts_pb2.ContainerAudio.WAV
                )
            ),
            unsafe_mode=True,
            # Параметры синтеза
            hints=[
                tts_pb2.Hints(voice=voice),  # (Опционально) Задайте голос. Значение по умолчанию marina
                # (Опционально) Укажите амплуа, только если голос их имеет
                tts_pb2.Hints(speed=speed)  # (Опционально) Задайте скорость синтеза

            ],

            loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS
        )
    else:
        request = tts_pb2.UtteranceSynthesisRequest(

            text=text,
            output_audio_spec=tts_pb2.AudioFormatOptions(
                container_audio=tts_pb2.ContainerAudio(
                    container_audio_type=tts_pb2.ContainerAudio.WAV
                )
            ),
            unsafe_mode=True,
            # Параметры синтеза
            hints=[
                tts_pb2.Hints(voice=voice),  # (Опционально) Задайте голос. Значение по умолчанию marina
                # (Опционально) Укажите амплуа, только если голос их имеет
                tts_pb2.Hints(speed=speed),  # (Опционально) Задайте скорость синтеза
                tts_pb2.Hints(role=role)
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
        ('authorization', f'Api-Key {YANDEX_SPEECH_KEY}'),
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
