FROM python:3.12-slim

WORKDIR /app

# Устанавливаем FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем необходимые папки
RUN mkdir -p downloads

# Запускаем универсальный запускатель (оба бота)
CMD ["python", "run_bots.py"]
