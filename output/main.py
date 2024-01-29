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




class VoiceSelection(StatesGroup):
    Choosing = State()


API_TOKEN = TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


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

@dp.message_handler(commands=['developer'], state="*")
async def handle_developer(message: types.Message):
    # Текст с ссылкой на разработчика
    developer_text = "Привет! Я создан и поддерживаюсь Тимерланом. Если у тебя есть вопросы или предложения, " \
                     "ты можешь написать ему в телеграм: [Тимерлан](https://t.me/timaadev) 🤖"
    
    # Отправляем текст и преобразуем его в речь
    await bot.send_message(message.chat.id, developer_text, parse_mode=ParseMode.MARKDOWN)

def synthesize(api_key, text,voice) -> pydub.AudioSegment: 
    request = tts_pb2.UtteranceSynthesisRequest(
        text=text,
        output_audio_spec=tts_pb2.AudioFormatOptions(
            container_audio=tts_pb2.ContainerAudio(
                container_audio_type=tts_pb2.ContainerAudio.WAV
            )
        ),
        # Параметры синтеза
       hints=[
    tts_pb2.Hints(voice=voice),  # (Опционально) Задайте голос. Значение по умолчанию marina
          # (Опционально) Укажите амплуа, только если голос их имеет
    tts_pb2.Hints(speed=1.1)           # (Опционально) Задайте скорость синтеза
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


async def check_sub_channels(channels,user_id):
    for channels in channels:
        chat_member = await bot.get_chat_member(chat_id= channels[1],user_id=user_id)
        if chat_member['status'] == 'left':
            return False
        return True
    


@dp.message_handler(content_types=types.ContentTypes.TEXT, state="*")
async def handle_text_message(message: types.Message, state: FSMContext):
    api_key = 'AQVN0fiGepILDWchpaGpBf81jITFo_SQY6AruXBb'  # Замените на свой API-ключ
    text = message.text
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Немонтаж 🎨',url='https://t.me/dfdfdfrrr'))
    if await check_sub_channels(channels=CNANNELS, user_id=message.from_user.id):

        # Сохраните текст в состоянии пользователя
        await state.update_data(text=text)

        # Войти в состояние выбора голоса
        await VoiceSelection.Choosing.set()

        # Отправить клавиатуру с выбором голоса
        await bot.send_message(message.chat.id, "Выберите голос:", reply_markup=generate_voice_keyboard())
    else:
        await bot.send_message(message.chat.id, text=NOT_SUB_MESSAGE,reply_markup=keyboard,parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data.startswith('voice_'), state=VoiceSelection.Choosing)
async def process_voice_choice(callback_query: types.CallbackQuery, state: FSMContext):
    # Извлечь выбранный голос из данных колбэка
    selected_voice = callback_query.data.split('_')[1]

    # Извлечь текст из состояния пользователя
    data = await state.get_data()
    text = data['text']

    # Используйте выбранный голос для синтеза речи
    api_key = 'AQVN0fiGepILDWchpaGpBf81jITFo_SQY6AruXBb'  # Замените на свой API-ключ

    audio = synthesize(api_key, text[0:249], voice=selected_voice)

    # Отправка голосового сообщения
    with io.BytesIO() as audio_buffer:
        audio.export(audio_buffer, format='wav')
        audio_buffer.seek(0)
        await bot.send_voice(callback_query.from_user.id, audio_buffer, caption=text[0:259] + '....',
                             parse_mode=ParseMode.MARKDOWN)

    # Выйти из состояния выбора голоса
    await state.finish()

    # Ответить на колбэк, чтобы закрыть всплывающее окно с выбором голоса
    await bot.answer_callback_query(callback_query.id, text=f"Выбран голос: {selected_voice}")
if __name__ == '__main__':
    from aiogram import executor

    loop = asyncio.get_event_loop()
    loop.create_task(bot.send_message(5455171373, 'Бот запущен'))  # Замените 123456789 на ваш ID чата
    executor.start_polling(dp, skip_updates=True)
