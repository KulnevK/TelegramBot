import os
import logging
import asyncio
import threading
from bot import main as telegram_main
from vk_bot import main as vk_main

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("Запуск Telegram бота...")
        telegram_main()
    except Exception as e:
        logger.error(f"Ошибка Telegram бота: {e}")


def run_vk_bot():
    """Запуск VK бота"""
    try:
        logger.info("Запуск VK бота...")
        vk_main()
    except Exception as e:
        logger.error(f"Ошибка VK бота: {e}")


def main():
    """Запуск обоих ботов"""
    logger.info("Запуск универсального бота...")

    # Проверяем наличие токенов
    has_telegram = bool(os.getenv("BOT_TOKEN"))
    has_vk = bool(os.getenv("VK_TOKEN"))

    if not has_telegram and not has_vk:
        logger.error("Не установлены токены! Установите BOT_TOKEN и/или VK_TOKEN")
        return

    threads = []

    # Запускаем Telegram бота в отдельном потоке
    if has_telegram:
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
        threads.append(telegram_thread)
        logger.info("✅ Telegram бот запущен")
    else:
        logger.warning("⚠️ BOT_TOKEN не установлен, Telegram бот не запущен")

    # Запускаем VK бота в отдельном потоке
    if has_vk:
        vk_thread = threading.Thread(target=run_vk_bot, daemon=True)
        vk_thread.start()
        threads.append(vk_thread)
        logger.info("✅ VK бот запущен")
    else:
        logger.warning("⚠️ VK_TOKEN не установлен, VK бот не запущен")

    # Ждём завершения всех потоков
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        logger.info("Остановка ботов...")


if __name__ == '__main__':
    main()
