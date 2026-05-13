import os
import logging
import asyncio
import threading
import sys

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def run_vk_bot():
    """Запуск VK бота"""
    try:
        from vk_bot import main as vk_main
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

    # Если есть только Telegram - запускаем его в главном потоке
    if has_telegram and not has_vk:
        from bot import main as telegram_main
        logger.info("Запуск только Telegram бота...")
        telegram_main()
        return

    # Если есть только VK - запускаем его в главном потоке
    if has_vk and not has_telegram:
        logger.info("Запуск только VK бота...")
        run_vk_bot()
        return

    # Если есть оба - запускаем VK в отдельном потоке, Telegram в главном
    if has_telegram and has_vk:
        logger.info("Запуск обоих ботов...")

        # VK бот в отдельном потоке
        vk_thread = threading.Thread(target=run_vk_bot, daemon=True)
        vk_thread.start()
        logger.info("✅ VK бот запущен в отдельном потоке")

        # Telegram бот в главном потоке
        from bot import main as telegram_main
        logger.info("Запуск Telegram бота в главном потоке...")
        telegram_main()


if __name__ == '__main__':
    main()
