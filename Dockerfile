# Используем стабильный Python 3.11
FROM python:3.11-slim

# Устанавливаем зависимости для сборки и pip
RUN apt-get update && apt-get install -y gcc g++ git build-essential libffi-dev libssl-dev && \
    pip install --upgrade pip setuptools wheel

# Создаём рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY requirements.txt .
COPY bot.py .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Переменные окружения (можно задать на Render)
# ENV TOKEN=<ваш токен>
# ENV ADMIN_ID=<ваш ID>

# Команда запуска бота
CMD ["python", "bot.py"]
