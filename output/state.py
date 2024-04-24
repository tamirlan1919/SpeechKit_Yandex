from aiogram.dispatcher.filters.state import State, StatesGroup

class VoiceSelection(StatesGroup):
    Choosing = State()
    FormatChoosing = State()

class NewsletterText(StatesGroup):
    text = State()

class UpdateSymbols(StatesGroup):
    symbols = State()

class UpdateMonth(StatesGroup):
    month = State()

class SearchUserState(StatesGroup):
    InputUsername = State()

class BonusDayState(StatesGroup):
    bonus = State()


class BonusRefState(StatesGroup):
    ref = State()