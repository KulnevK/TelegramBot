import os
import logging
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from database import Database
from music_downloader import MusicDownloader
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен VK группы (из переменной окружения)
VK_TOKEN = os.getenv("VK_TOKEN")

# Папка для временных файлов
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# База данных
db = Database()

# Загрузчик музыки
music_dl = MusicDownloader()

# ID администраторов
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()]


def is_valid_url(url):
    """Проверка, является ли текст ссылкой на видео или музыку"""
    import re
    patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)',
        r'(https?://)?(www\.)?(tiktok\.com)',
        r'(https?://)?(www\.)?(instagram\.com)',
        r'(https?://)?(www\.)?(twitter\.com|x\.com)',
        r'(https?://)?(www\.)?(facebook\.com)',
        r'(https?://)?(www\.)?music\.yandex',
        r'(https?://)?(www\.)?(soundcloud\.com)',
        r'(https?://)?(www\.)?(bandcamp\.com)',
    ]
    return any(re.search(pattern, url) for pattern in patterns)


async def download_video(url):
    """Скачивание видео по ссылке"""
    import yt_dlp

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename, info.get('title', 'Видео')

        result = await asyncio.to_thread(download)
        return result
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None, None


def send_message(vk, user_id, message):
    """Отправка сообщения пользователю"""
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=get_random_id()
    )


def send_document(vk, user_id, file_path, title):
    """Отправка файла пользователю"""
    try:
        # Загружаем файл на сервер VK
        upload = vk_api.VkUpload(vk)
        doc = upload.document_message(file_path, title=title, peer_id=user_id)

        # Отправляем документ
        vk.messages.send(
            user_id=user_id,
            attachment=f"doc{doc['doc']['owner_id']}_{doc['doc']['id']}",
            random_id=get_random_id()
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки файла: {e}")
        return False


async def handle_message(vk, event):
    """Обработчик сообщений"""
    user_id = event.user_id
    text = event.text.strip()

    # Команда /start
    if text.lower() in ['/start', 'начать', 'start']:
        db.add_user(user_id, None, None)
        stats = db.get_user_stats(user_id)

        premium_status = ""
        if stats['is_premium']:
            premium_status = "\n\n💎 У вас активен премиум!"
        else:
            premium_status = f"\n\n📊 Скачиваний сегодня: {stats['downloads_today']}/3"

        send_message(vk, user_id,
            "Привет! 👋\n\n"
            "Я бот для скачивания видео и музыки из социальных сетей!\n\n"
            "Поддерживаю:\n"
            "🎥 Видео:\n"
            "✅ YouTube\n"
            "✅ TikTok\n"
            "✅ Instagram\n"
            "✅ Twitter/X\n"
            "✅ Facebook\n\n"
            "🎵 Музыка:\n"
            "✅ Яндекс.Музыка\n"
            "✅ SoundCloud\n"
            "✅ Bandcamp\n\n"
            "Просто отправь мне ссылку!\n\n"
            f"{premium_status}\n\n"
            "Команды:\n"
            "/start - начать работу\n"
            "/help - помощь\n"
            "/stats - моя статистика"
        )
        return

    # Команда /help
    if text.lower() in ['/help', 'помощь', 'help']:
        send_message(vk, user_id,
            "Как использовать бота:\n\n"
            "1. Скопируйте ссылку на видео или музыку\n"
            "2. Отправьте её мне\n"
            "3. Подождите немного\n"
            "4. Получите файл!\n\n"
            "🎥 Видео:\n"
            "• YouTube\n"
            "• TikTok\n"
            "• Instagram\n"
            "• Twitter/X\n"
            "• Facebook\n\n"
            "🎵 Музыка:\n"
            "• Яндекс.Музыка\n"
            "• SoundCloud\n"
            "• Bandcamp\n\n"
            "🆓 Бесплатно: 3 скачивания в день"
        )
        return

    # Команда /stats
    if text.lower() in ['/stats', 'статистика', 'stats']:
        stats = db.get_user_stats(user_id)

        if not stats:
            send_message(vk, user_id, "Ошибка получения статистики")
            return

        status = "💎 Премиум" if stats['is_premium'] else "🆓 Бесплатный"

        if user_id in ADMIN_IDS:
            status = "👑 Администратор"

        send_message(vk, user_id,
            f"📊 Ваша статистика:\n\n"
            f"Статус: {status}\n"
            f"Скачиваний сегодня: {stats['downloads_today']}/{'∞' if user_id in ADMIN_IDS else '3'}\n"
            f"Всего скачано: {stats['total_downloads']}"
        )
        return

    # Обработка ссылок
    if not is_valid_url(text):
        send_message(vk, user_id,
            "Это не похоже на ссылку на видео или музыку 🤔\n\n"
            "Отправьте ссылку с поддерживаемых платформ:\n"
            "🎥 YouTube, TikTok, Instagram, Twitter, Facebook\n"
            "🎵 Яндекс.Музыка, SoundCloud, Bandcamp"
        )
        return

    # Проверяем лимиты
    if user_id not in ADMIN_IDS:
        can_download, message = db.can_download(user_id)

        if not can_download:
            send_message(vk, user_id, f"❌ {message}")
            return

    # Определяем тип контента
    is_music = music_dl.is_music_url(text)

    if is_music:
        send_message(vk, user_id, "⏳ Скачиваю музыку...")
    else:
        send_message(vk, user_id, "⏳ Скачиваю видео...")

    try:
        if is_music:
            # Скачивание музыки
            if music_dl.is_yandex_music_url(text):
                filename, title = await music_dl.download_yandex_music(text)
            else:
                filename, title = await music_dl.download_music_generic(text)

            if filename and os.path.exists(filename):
                file_size = os.path.getsize(filename)

                if file_size > 50 * 1024 * 1024:
                    send_message(vk, user_id,
                        "❌ Файл слишком большой (больше 50 МБ).\n"
                        "VK не позволяет отправлять такие большие файлы."
                    )
                    os.remove(filename)
                    return

                send_message(vk, user_id, "📤 Отправляю музыку...")

                if send_document(vk, user_id, filename, f"{title}.mp3"):
                    db.increment_download(user_id)
                    os.remove(filename)
                else:
                    send_message(vk, user_id, "❌ Ошибка отправки файла")
                    os.remove(filename)
            else:
                send_message(vk, user_id,
                    "❌ Не удалось скачать музыку.\n"
                    "Возможно, трек недоступен или ссылка неверная."
                )

        else:
            # Скачивание видео
            filename, title = await download_video(text)

            if filename and os.path.exists(filename):
                file_size = os.path.getsize(filename)

                if file_size > 50 * 1024 * 1024:
                    send_message(vk, user_id,
                        "❌ Видео слишком большое (больше 50 МБ).\n"
                        "VK не позволяет отправлять такие большие файлы."
                    )
                    os.remove(filename)
                    return

                send_message(vk, user_id, "📤 Отправляю видео...")

                if send_document(vk, user_id, filename, f"{title}.mp4"):
                    db.increment_download(user_id)
                    os.remove(filename)
                else:
                    send_message(vk, user_id, "❌ Ошибка отправки файла")
                    os.remove(filename)
            else:
                send_message(vk, user_id,
                    "❌ Не удалось скачать видео.\n"
                    "Возможно, видео приватное или ссылка неверная."
                )

    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        send_message(vk, user_id,
            "❌ Произошла ошибка при скачивании.\n"
            "Попробуйте другую ссылку или повторите позже."
        )


def main():
    """Запуск VK бота"""
    if not VK_TOKEN:
        logger.error("VK_TOKEN не установлен в переменных окружения!")
        return

    logger.info("Запуск VK бота...")

    # Авторизация
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logger.info("VK бот запущен и готов к работе!")

    # Обработка событий
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                asyncio.run(handle_message(vk, event))
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")


if __name__ == '__main__':
    main()
