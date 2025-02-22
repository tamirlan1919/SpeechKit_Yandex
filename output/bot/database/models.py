from sqlalchemy import (Column, Integer, String, ForeignKey,
                        Float, TIMESTAMP, Boolean, BigInteger,
                        DateTime, Numeric)
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.orm import relationship


Base = declarative_base()


### Таблица пользователей
class User(Base):
    __tablename__ = "my_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False)
    subscription_date = Column(DateTime, default=datetime.datetime.utcnow)
    count_symbol = Column(Integer, default=0)
    request_month = Column(Integer, default=0)
    unlimited = Column(String, default="OFF")
    status = Column(String, default="active")
    role = Column(String, default="user")


### Таблица настроек пользователей
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("my_users.user_id"), unique=True, nullable=False)
    selected_voice = Column(String, default="default")
    selected_speed = Column(Float, default=1.0)
    format = Column(String, default="mp3")
    role = Column(String, default='undefined')


### Таблица подписок
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("my_users.user_id"), nullable=False)
    total_symbols = Column(Integer, default=0)
    email = Column(String)
    phone = Column(String)
    tariff_name = Column(String)
    status = Column(String, default="active")
    purchase_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="subscription")


class Transaction(Base):
    """Таблица для хранения всех платежей"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("my_users.user_id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    amount = Column(Numeric(10, 2), nullable=False)  # Сумма платежа (например, 150.00)
    currency = Column(String, default="RUB")  # Валюта платежа
    tariff_name = Column(String, nullable=False)  # Название тарифа
    total_symbols = Column(Integer, nullable=False)  # Сколько символов добавлено

    status = Column(String, default="completed")  # "completed", "failed"
    transaction_id = Column(String, nullable=True, unique=True)  # ID транзакции в платежной системе
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    # Связь с подпиской
    subscription = relationship("Subscription", back_populates="transactions")


### Таблица бонусов за день
class BonusDay(Base):
    __tablename__ = "bonus_day"

    id = Column(Integer, primary_key=True)
    count = Column(Integer, default=25)


### Таблица бонусов за реферальную программу
class BonusRef(Base):
    __tablename__ = "bonus_ref"

    id = Column(Integer, primary_key=True)
    count = Column(Integer, default=10)


### Таблица реферальных данных
class Referral(Base):
    __tablename__ = "ref_table"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("my_users.user_id"), nullable=False)
    invited_user_id = Column(BigInteger, ForeignKey("my_users.user_id"))
    count_request_month = Column(Integer, default=0)


### Таблица активности пользователей
class ActivityToday(Base):
    __tablename__ = "activity_today"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("my_users.user_id"), nullable=False)
    last_activity_date = Column(DateTime, default=datetime.datetime.utcnow)  # Тип DateTime


