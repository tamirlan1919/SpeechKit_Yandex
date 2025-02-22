FROM python:3.10

# Копируем всю папку output в контейнер в директорию /app
WORKDIR /app
COPY output /app/output

# Устанавливаем PYTHONPATH так, чтобы корневая папка (где находится output) была видна
ENV PYTHONPATH="/app"

# Задаём рабочую директорию для backend
WORKDIR /app/output/backend

# Устанавливаем зависимости (requirements.txt находится внутри output/backend)
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем приложение (убедитесь, что app.py содержит объект app)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
