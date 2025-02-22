import datetime
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
# Импортируем модели – предполагается, что они уже определены
from .engine_redis import redis
from .models import (
    User,
    UserSettings,
    Subscription,
    BonusDay,
    BonusRef,
    Referral,
    ActivityToday, Transaction
)


# ==============================
# CRUD для настроек пользователя
# ==============================

async def get_user_settings(user_id: int, db: AsyncSession):
    """Получить настройки пользователя по user_id.
       Возвращает dict с ключами: selected_voice, selected_speed, format, role (если есть) или None."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings_obj = result.scalars().first()
    if settings_obj:
        return {
            'selected_voice': settings_obj.selected_voice,
            'selected_speed': settings_obj.selected_speed,
            'format': settings_obj.format,
            'role': getattr(settings_obj, 'role', None)  # если поле role существует
        }
    return None


async def save_user_settings(user_id: int, voice: str, speed: float, format_: str, db: AsyncSession):
    """Сохранить или обновить настройки пользователя."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings_obj = result.scalars().first()
    if settings_obj:
        settings_obj.selected_voice = voice
        settings_obj.selected_speed = speed
        settings_obj.format = format_
    else:
        settings_obj = UserSettings(user_id=user_id, selected_voice=voice, selected_speed=speed, format=format_)
        db.add(settings_obj)
    await db.commit()
    return settings_obj


# ==============================
# CRUD для пользователей
# ==============================

async def add_user(user_id: int, name: str, subscription_date, count_symbol: int,
                   request_month: int, unlimited: str, status: str, role: str, db: AsyncSession):
    """Добавить нового пользователя, если его ещё нет."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    existing = result.scalars().first()
    if existing:
        return
    subscription_date = datetime.datetime.strptime("2025-02-12 00:45:49", "%Y-%m-%d %H:%M:%S")
    new_user = User(
        user_id=user_id,
        name=name,
        subscription_date=subscription_date,
        count_symbol=count_symbol,
        request_month=request_month,
        unlimited=unlimited,
        status=status,
        role=role
    )
    db.add(new_user)
    await db.commit()


async def count_total_users(db: AsyncSession):
    """Подсчитать общее количество пользователей."""
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar()


async def get_all_user_ids(db: AsyncSession):
    """Получить список всех user_id из таблицы пользователей."""
    result = await db.execute(select(User.user_id))
    user_ids = result.scalars().all()
    print(user_ids)
    return user_ids


async def count_new_users_this_month(db: AsyncSession):
    """Подсчитать количество новых пользователей за текущий месяц."""
    current_month = datetime.datetime.utcnow().strftime("%Y-%m")
    result = await db.execute(
        select(User).where(func.to_char(User.subscription_date, 'YYYY-MM').like(f"{current_month}%"))
    )
    users = result.scalars().all()
    return len(users)


async def count_new_users_last_month(db: AsyncSession):
    """Подсчитать количество новых пользователей за прошлый месяц."""
    current_date = datetime.datetime.utcnow()
    first_day_current_month = current_date.replace(day=1)
    last_day_last_month = first_day_current_month - datetime.timedelta(days=1)
    last_month = last_day_last_month.strftime("%Y-%m")
    result = await db.execute(
        select(User).where(func.to_char(User.subscription_date, 'YYYY-MM').like(f"{last_month}%"))
    )
    users = result.scalars().all()
    return len(users)


# ==============================
# CRUD для активности
# ==============================

async def count_active_users_today(db: AsyncSession):
    """Подсчитать количество активных пользователей за сегодня."""
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    result = await db.execute(
        select(ActivityToday).where(func.to_char(ActivityToday.last_activity_date, 'YYYY-MM-DD') == today_str)
    )
    activities = result.scalars().all()
    return len(activities)


async def insert_or_update_user(user_id: int, db: AsyncSession):
    """Вставить или обновить запись активности для пользователя."""
    result = await db.execute(select(ActivityToday).where(ActivityToday.user_id == user_id))
    activity = result.scalars().first()
    if activity:
        activity.last_activity_date = datetime.datetime.utcnow()
    else:
        activity = ActivityToday(user_id=user_id, last_activity_date=datetime.datetime.utcnow())
        db.add(activity)
    await db.commit()


async def add_daily_requests(db: AsyncSession):
    """Обновить поле request_month у всех пользователей, используя значение из таблицы bonus_day или 25 по умолчанию."""

    result = await db.execute(select(BonusDay))
    bonus = result.scalars().first()
    new_request_month = bonus.count if bonus else 6
    result = await db.execute(select(User))
    users = result.scalars().all()
    for user in users:
        user.request_month = new_request_month
    await db.commit()


async def get_all_users(db: AsyncSession):
    """Получить список всех пользователей (user_id и name)."""
    result = await db.execute(select(User.user_id, User.name))
    return result.all()


# ==============================
# CRUD для бонусов
# ==============================

async def insert_bonus(db: AsyncSession):
    """Вставить запись в таблицу bonus_day, если она отсутствует."""
    result = await db.execute(select(BonusDay))
    bonus = result.scalars().first()
    if bonus:
        return
    bonus = BonusDay(count=25)
    db.add(bonus)
    await db.commit()


async def insert_ref_bonus(db: AsyncSession):
    """Вставить запись в таблицу bonus_ref, если она отсутствует."""
    result = await db.execute(select(BonusRef))
    bonus = result.scalars().first()
    if bonus:
        return
    bonus = BonusRef(count=10)
    db.add(bonus)
    await db.commit()


async def update_bonus(count: int, db: AsyncSession):
    """Обновить бонус в таблице bonus_day и установить у всех пользователей request_month = count."""
    result = await db.execute(select(BonusDay))
    bonus = result.scalars().first()
    if bonus:
        bonus.count = count
    else:
        bonus = BonusDay(count=count)
        db.add(bonus)
    result = await db.execute(select(User))
    users = result.scalars().all()
    for user in users:
        user.request_month = count
    await db.commit()


async def get_request_monthALL(db: AsyncSession):
    """Получить значение count из таблицы bonus_day."""
    result = await db.execute(select(BonusDay))
    bonus = result.scalars().first()
    return bonus.count if bonus else None


# ==============================
# CRUD для символов
# ==============================

async def get_count_symbol(user_id: int, db: AsyncSession):
    """Получить count_symbol для указанного user_id."""
    result = await db.execute(select(User.count_symbol).where(User.user_id == user_id))
    return result.scalar()


async def get_count_symbol_all(db: AsyncSession):
    """Получить count_symbol для пользователя с id = 4."""
    result = await db.execute(select(User.count_symbol).where(User.id == 4))
    return result.scalar()


async def update_count_symbol(count: int, db: AsyncSession):
    """Обновить поле count_symbol для всех пользователей."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    for user in users:
        user.count_symbol = count
    await db.commit()


# ==============================
# CRUD для бонуса рефералов
# ==============================

async def update_bonus_ref(count: int, db: AsyncSession):
    """Обновить бонус за реферальную ссылку в таблице bonus_ref."""
    result = await db.execute(select(BonusRef))
    bonus = result.scalars().first()
    if bonus:
        bonus.count = count
    else:
        bonus = BonusRef(count=count)
        db.add(bonus)
    await db.commit()


async def get_bonus_ref(db: AsyncSession):
    """Получить запись из таблицы bonus_ref."""
    result = await db.execute(select(BonusRef.count))
    return result.scalars().first() or 5


# ==============================
# CRUD для обновления символов и запросов
# ==============================

async def update_user_symbols(user_id: int, new_symbols: int, db: AsyncSession):
    """Обновить count_symbol для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.count_symbol = new_symbols
        await db.commit()


async def get_symbols(user_id: int, db: AsyncSession):

    result = await db.execute(
        select(User.count_symbol).where(User.user_id == int(user_id))
    )
    balance = result.scalar()
    return balance


async def update_user_request_month(user_id: int, new_request_month: int, db: AsyncSession):
    """Обновить request_month для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.request_month = new_request_month
        await db.commit()


async def get_request_month(user_id: int, db: AsyncSession):
    """Получить request_month для указанного пользователя."""
    result = await db.execute(select(User.request_month).where(User.user_id == int(user_id)))
    return result.scalar()


# ==============================
# CRUD для реферальных бонусов и ограничений
# ==============================

async def get_bonus_user_ref(user_id: int, db: AsyncSession):
    """Получить count_request_month из таблицы рефералов для указанного пользователя."""
    result = await db.execute(select(Referral.count_request_month).where(Referral.user_id == user_id))
    value = result.scalar()
    return value if value is not None else 0


async def get_unlimited_person(user_id: int, db: AsyncSession):
    """Получить значение поля unlimited для указанного пользователя."""
    result = await db.execute(select(User.unlimited).where(User.user_id == int(user_id)))
    return result.scalar()


async def update_unlimited_on(user_id: int, db: AsyncSession):
    """Установить unlimited = 'ON' для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.unlimited = 'ON'
        await db.commit()


async def update_unlimited_off(user_id: int, db: AsyncSession):
    """Установить unlimited = 'OFF' для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.unlimited = 'OFF'
        await db.commit()


# ==============================
# CRUD для ролей и статусов
# ==============================

async def get_role_user(user_id: int, db: AsyncSession):
    """Получить роль для указанного пользователя."""
    result = await db.execute(select(User.role).where(User.user_id == user_id))
    return result.scalar()


async def get_status_user(user_id: int, db: AsyncSession):
    """Получить статус для указанного пользователя."""
    result = await db.execute(select(User.status).where(User.user_id == user_id))
    return result.scalar()


async def update_role_user_admin(user_id: int, db: AsyncSession):
    """Установить роль 'admin' для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.role = 'admin'
        await db.commit()


async def update_role_user_person(user_id: int, db: AsyncSession):
    """Установить роль 'user' для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.role = 'user'
        await db.commit()


async def update_status_kick(user_id: int, db: AsyncSession):
    """Установить статус 'kick' для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.status = 'kick'
        await db.commit()


async def update_status_join(user_id: int, db: AsyncSession):
    """Установить статус 'join' для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.status = 'join'
        await db.commit()


async def get_all_admin_from_bd(db: AsyncSession):
    """Подсчитать количество пользователей с ролью 'admin'."""
    result = await db.execute(select(func.count()).select_from(User).where(User.role == 'admin'))
    return result.scalar()


async def get_admin_user(user_id: int, db: AsyncSession):
    """Получить роль пользователя по user_id (ожидается, что 'admin' или другое значение)."""
    result = await db.execute(select(User.role).where(User.user_id == user_id))
    return result.scalar()


# ==============================
# CRUD для уменьшения значений
# ==============================

async def minus_one(user_id: int, db: AsyncSession):
    """Уменьшить request_month на 1 для указанного пользователя."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user:
        user.request_month = user.request_month - 1
        await db.commit()


async def minus_one_bonus(user_id: int, db: AsyncSession):
    """Уменьшить count_request_month на 1 в таблице рефералов для указанного пользователя."""
    result = await db.execute(select(Referral).where(Referral.user_id == user_id))
    referral = result.scalars().first()
    if referral:
        referral.count_request_month = referral.count_request_month - 1
        await db.commit()


# ==============================
# Остальные функции
# ==============================

async def count_blocked_users(db: AsyncSession):
    """Подсчитать количество пользователей, у которых статус 'sent'."""
    result = await db.execute(select(func.count()).select_from(User).where(User.status == 'sent'))
    return result.scalar()


async def create_invitation_record(referrer_id: int, invited_user_id: int, session: AsyncSession):
    # Проверяем, что пользователь не приглашает самого себя
    if referrer_id == invited_user_id:
        return None

    # Проверяем, существует ли уже этот user_id в таблице (то есть, был ли он уже зарегистрирован)
    existing_user_result = await session.execute(
        select(Referral).filter_by(user_id=invited_user_id)
    )
    existing_user = existing_user_result.scalar_one_or_none()

    if existing_user:
        # Если приглашённый уже есть в системе, не создаём дубликат
        return None

    # Получаем значение бонуса из таблицы BonusRef
    bonus_result = await session.execute(select(BonusRef.count))
    bonus = bonus_result.scalar_one_or_none() or 0

    # Проверяем, есть ли запись у реферера (если есть, прибавляем бонус)
    referrer_record_result = await session.execute(
        select(Referral).filter_by(user_id=referrer_id)
    )
    referrer_record = referrer_record_result.scalar_one_or_none()

    if referrer_record:
        # Если запись уже есть, прибавляем бонус
        referrer_record.count_request_month += bonus
    else:
        # Если записи нет, создаем новую запись для реферера
        referrer_record = Referral(
            user_id=referrer_id,
            invited_user_id=None,  # Поле можно оставить пустым
            count_request_month=bonus
        )
        session.add(referrer_record)

    # Добавляем приглашённого **только если его нет**
    invited_entry = Referral(
        user_id=invited_user_id,
        invited_user_id=referrer_id,
        count_request_month=0
    )
    session.add(invited_entry)

    await session.commit()
    return referrer_record


async def create_referral_profile(user_id: int, session: AsyncSession):
    # Можно добавить проверку: существует ли уже профиль для данного пользователя
    result = await session.execute(select(Referral).where(User.user_id == user_id))
    existing = result.scalars().first()
    if existing:
        return
    referral_profile = Referral(
        user_id=user_id,
        invited_user_id=None,
        count_request_month=0
    )
    session.add(referral_profile)
    await session.commit()
    return referral_profile


async def get_invited_users(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(func.count())  # Запрашиваем только ID приглашенных
        .filter(Referral.invited_user_id == user_id)
    )
    return result.scalar() or 0



async def get_request_mon_for_user(user_id: int, session: AsyncSession):
    # Получаем сумму запросов за месяц из таблицы ref_table (Referral)
    result = await session.execute(
        select(func.sum(Referral.count_request_month)).filter(Referral.user_id == user_id)
    )
    total = result.scalar()
    return total or 0  # Если None, возвращаем 0

#Обработка платежей
async def process_payment(user_id: int, total_symbols: int, email: str,
                          phone: str, tariff_name: str,amount: float,
                          currency: str, transaction_id: str, session: AsyncSession):
    """Обрабатывает платеж, обновляет подписку и сохраняет транзакцию в базе данных."""

    # 🔹 Проверяем, существует ли пользователь в my_users
    result = await session.execute(select(User).filter_by(user_id=user_id))
    user_exists = result.scalars().first()

    if not user_exists:
        print(f"❌ Ошибка: пользователя с user_id={user_id} нет в базе!")
        return  # Останавливаем выполнение, чтобы не нарушить ForeignKey

    # 🔹 Сохраняем транзакцию в transactions
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        currency=currency,
        tariff_name=tariff_name,
        total_symbols=total_symbols,
        transaction_id=transaction_id,
        status="completed"
    )
    session.add(transaction)
    await session.flush()  # Нужно для получения transaction.id

    # 🔹 Обновляем подписку пользователя
    result = await session.execute(select(Subscription).filter_by(user_id=user_id))
    subscription = result.scalars().first()

    if subscription:
        subscription.total_symbols += total_symbols
        subscription.tariff_name = tariff_name
        subscription.purchase_date = datetime.datetime.utcnow()
    else:
        subscription = Subscription(
            user_id=user_id,
            total_symbols=total_symbols,
            email=email,
            phone=phone,
            tariff_name=tariff_name,
            status="active",
            purchase_date=datetime.datetime.utcnow(),
        )
        session.add(subscription)

    # 🔹 Привязываем транзакцию к подписке
    transaction.subscription_id = subscription.id

    # ✅ Фиксируем изменения в БД
    await session.commit()


async def get_symbols_from_subscriptions(user_id: int, session: AsyncSession):
    """Функция для получения токенов определенного пользователя"""
    result = await session.execute(select(Subscription.total_symbols).filter_by(user_id=user_id))
    total_symbols = result.scalar()
    return total_symbols if total_symbols is not None else 0


async def update_subscriptions_symbols_by_id(user_id: int, count: int, session: AsyncSession):
    try:
        result = await session.execute(select(Subscription).filter_by(user_id=user_id))
        data = result.scalars().first()

        if data:
            if data.total_symbols >= count:
                data.total_symbols -= count
                await session.flush()  # Промежуточный сброс изменений
                await session.commit()
                await session.refresh(data)  # Обновляем объект после коммита
            else:
                print(f"Недостаточно символов у пользователя {user_id} для списания {count} символов")
        else:
            print(f"Пользователь с id={user_id} не найден в таблице Subscription")

    except Exception as e:
        await session.rollback()  # В случае ошибки откатываем изменения
        print(f"Ошибка при обновлении подписки: {e}")