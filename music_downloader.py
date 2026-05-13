import os
import logging
import yt_dlp
from yandex_music import Client

logger = logging.getLogger(__name__)

DOWNLOAD_FOLDER = "downloads"

class MusicDownloader:
    def __init__(self):
        self.yandex_client = None
        self.yandex_token = os.getenv("YANDEX_MUSIC_TOKEN")

    def init_yandex_client(self, token=None):
        """Инициализация клиента Яндекс.Музыки"""
        try:
            # Используем токен из параметра, переменной окружения или без токена
            token_to_use = token or self.yandex_token
            if token_to_use:
                self.yandex_client = Client(token_to_use).init()
            else:
                self.yandex_client = Client().init()
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Яндекс.Музыки: {e}")
            return False

    async def download_yandex_music(self, url):
        """Скачивание с Яндекс.Музыки"""
        import asyncio

        try:
            if not self.yandex_client:
                self.init_yandex_client()

            # Извлекаем ID трека из URL
            track_id = self._extract_yandex_track_id(url)
            if not track_id:
                return None, None

            # Выполняем синхронные операции в отдельном потоке
            def download():
                # Получаем информацию о треке
                track = self.yandex_client.tracks([track_id])[0]

                # Формируем имя файла
                artist = track.artists[0].name if track.artists else "Unknown"
                title = track.title
                filename = os.path.join(DOWNLOAD_FOLDER, f"{artist} - {title}.mp3")

                # Скачиваем трек
                track.download(filename)

                return filename, f"{artist} - {title}"

            result = await asyncio.to_thread(download)
            return result

        except Exception as e:
            logger.error(f"Ошибка скачивания с Яндекс.Музыки: {e}")
            return None, None

    def _extract_yandex_track_id(self, url):
        """Извлечь ID трека из URL Яндекс.Музыки"""
        import re

        # Убираем параметры запроса (всё после ?)
        url = url.split('?')[0]

        # Паттерны для разных форматов URL
        patterns = [
            r'music\.yandex\.\w+/album/\d+/track/(\d+)',
            r'music\.yandex\.\w+/track/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def download_music_generic(self, url):
        """Скачивание музыки с других сервисов через yt-dlp"""
        import asyncio

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(artist)s - %(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        try:
            # Запускаем синхронный код в отдельном потоке
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    # Формируем имя файла
                    artist = info.get('artist', info.get('uploader', 'Unknown'))
                    title = info.get('title', 'Unknown')

                    # yt-dlp может изменить расширение на .mp3 после конвертации
                    base_filename = os.path.join(DOWNLOAD_FOLDER, f"{artist} - {title}")

                    # Ищем файл с любым расширением
                    for ext in ['.mp3', '.m4a', '.opus', '.webm']:
                        filename = base_filename + ext
                        if os.path.exists(filename):
                            return filename, f"{artist} - {title}"

                    # Если не нашли, используем оригинальное имя
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        return filename, f"{artist} - {title}"

                    return None, None

            # Выполняем в отдельном потоке, чтобы не блокировать event loop
            result = await asyncio.to_thread(download)
            return result

        except Exception as e:
            logger.error(f"Ошибка скачивания музыки: {e}")
            return None, None

    def is_yandex_music_url(self, url):
        """Проверка, является ли URL ссылкой на Яндекс.Музыку"""
        return 'music.yandex' in url.lower()

    def is_music_url(self, url):
        """Проверка, является ли URL ссылкой на музыку"""
        music_patterns = [
            r'music\.yandex',
            r'soundcloud\.com',
            r'bandcamp\.com',
        ]

        import re
        return any(re.search(pattern, url.lower()) for pattern in music_patterns)
