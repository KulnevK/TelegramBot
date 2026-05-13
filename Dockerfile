FROM python:3.12-slim

WORKDIR /app

# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем необходимые папки
RUN mkdir -p downloads

# Запускаем бота
CMD ["python", "bot.py"]
