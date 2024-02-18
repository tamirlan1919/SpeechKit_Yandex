import io
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

class VoiceSelection(StatesGroup):
    Choosing = State()
    FormatChoosing = State()

API_TOKEN = TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())



create_db()

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
    # Текст приветственного сообщения с эмодзи
    welcome_text = "Привет! Я бот, который может преобразовывать текст в речь. " \
                   "Просто отправь мне текст, и я создам для тебя голосовое сообщение! 🎤"
    
    # Отправляем текст и преобразуем его в речь
    await bot.send_message(message.chat.id, welcome_text)

@dp.message_handler(commands=['admin'], state="*")
async def handle_admin(message: types.Message):
    # Проверяем, является ли отправитель сообщения администратором
    print(message.chat.id in admin_ids)
    if message.chat.id not in admin_ids:
        await message.reply("У вас нет доступа к админ-панели.")
        return
    
    # Создание клавиатуры админ-панели
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="Состояние бота"), types.KeyboardButton(text="Рассылка"),
                 types.KeyboardButton(text="Аналитика"))

    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@dp.message_handler(commands=['set_voice'], state="*")
async def handle_setVoice(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1,resize_keyboard=True) #создаем клавиатуру
    webAppTest = types.WebAppInfo(url = "https://ui-telegrab-bot.vercel.app/") #создаем webappinfo - формат хранения url
    one_butt = types.KeyboardButton(text="Перейти", web_app=webAppTest) #создаем кнопку типа webapp
    keyboard.add(one_butt) #добавляем кнопки в клавиатуру


    # keyboard = types.ReplyKeyboardMarkup()
    # keyboard.add("Перейти", web_app=WebAppInfo(url = 'https://ui-telegrab-bot.vercel.app/'))
    await bot.send_message(message.chat.id, 'Вы должны выбрать голос', reply_markup=keyboard)

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
    api_key = 'AQVN0fiGepILDWchpaGpBf81jITFo_SQY6AruXBb'  # Замените на свой API-ключ
    text = message.text
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='rudhdheheh 🎨',url='https://t.me/rudhdheheh'))
    keyboard.add(types.InlineKeyboardButton(text='Немонтаж 🎥',url='https://t.me/nmntzh'))
    user_id = message.from_user.id
    user_settings = get_user_settings(user_id)  # Функция get_user_settings должна быть определена
    print(user_settings)
    if await check_sub_channels(channels=CNANNELS, user_id=user_id):

        if user_settings:
            selected_voice = user_settings['selected_voice']
            selected_speed = user_settings['selected_speed']
            selected_format = user_settings['format']

            # Используйте настройки пользователя для синтеза речи
            audio = synthesize(api_key, text=text[0:599], voice=selected_voice,speed=selected_speed)

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
                webAppTest = types.WebAppInfo(url = "https://ui-telegrab-bot.vercel.app/") #создаем webappinfo - формат хранения url
                one_butt = types.KeyboardButton(text="Перейти", web_app=webAppTest) #создаем кнопку типа webapp
                keyboard.add(one_butt) #добавляем кнопки в клавиатуру


                # keyboard = types.ReplyKeyboardMarkup()
                # keyboard.add("Перейти", web_app=WebAppInfo(url = 'https://ui-telegrab-bot.vercel.app/'))
                await bot.send_message(message.chat.id, 'Вы должны выбрать голос', reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id, text=NOT_SUB_MESSAGE,reply_markup=keyboard,parse_mode='HTML')

# async def generate_speed_keyboard():
#     keyboard = types.InlineKeyboardMarkup()
#     speeds = [str(i / 10.0) for i in range(1, 30)]  # Speeds from 0.1 to 2.9
#     for i in range(0, len(speeds), 3):
#         row = []
#         for speed in speeds[i:i+3]:
#             row.append(InlineKeyboardButton(text=speed, callback_data=f"speed_{speed}"))
#         keyboard.row(*row)
#     return keyboard


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


# @dp.callback_query_handler(lambda c: c.data.startswith('speed_'), state=VoiceSelection.SpeedChoosing)
# async def process_speed_choice(callback_query: types.CallbackQuery, state: FSMContext):
#     selected_speed = float(callback_query.data.split('_')[1])
#     await VoiceSelection.FormatChoosing.set()

#     # Save selected speed to state
#     await state.update_data(selected_speed=selected_speed)

#     # Send keyboard for format selection
#     keyboard = await generate_format_keyboard()  # Await the function
#     await bot.edit_message_text("Выберите формат аудио:", callback_query.message.chat.id,
#                                 callback_query.message.message_id, reply_markup=keyboard)



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


if __name__ == '__main__':
    from aiogram import executor
    loop = asyncio.get_event_loop()
    loop.create_task(bot.send_message(5455171373, 'Бот запущен'))  # Замените 123456789 на ваш ID чата
    executor.start_polling(dp, skip_updates=True)
