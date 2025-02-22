from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TOKEN')
PAYMENTS_PROVIDER_TOKEN = os.getenv('PAYMENTS_PROVIDER_TOKEN')
YANDEX_SPEECH_KEY = os.getenv('YANDEX_SPEECH_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
admin_ids = [
    5455171373,
    387161594

]

roleLabels = {
    "neutral": 'Нейтральный',
    "good": 'Радостный',
    "strict": 'Строгий',
    "evil": 'Злой',
    "friendly": 'Дружелюбный',
    "whisper": 'Шепот'
};
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
    'anton': 'Антон 👤',
    'madi': 'Madï👤',
    'amira': 'Amïra 💅',
    'nigora': 'Nigora 💅',
    'john': 'John 👤',
    'lea': 'Lea 💅'
}

state_bot = True
users_per_page = 3  # Установка количества пользователей на странице



