FROM python:3.10

# Копируем всю папку output в контейнер
WORKDIR /app
COPY output /app/output

# Устанавливаем PYTHONPATH, чтобы модуль output был доступен
ENV PYTHONPATH="/app"

# Задаём рабочую директорию для бота
WORKDIR /app/output/bot

# Устанавливаем зависимости (requirements.txt внутри output/bot)
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота (main.py – точка входа)
CMD ["python", "main.py"]
