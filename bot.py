import os
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
from database import Database
from payments import create_payment, PREMIUM_MONTH_PRICE

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8675205493:AAE9MTp6uUVEH3VaoJveXFFydKoS75XYIFk"

# Папка для временных файлов
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# База данных
db = Database()

# ID администраторов (замените на свой Telegram ID)
ADMIN_IDS = [5204496353]  # Ваш ID администратора

def is_valid_url(url):
    """Проверка, является ли текст ссылкой на видео"""
    patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)',
        r'(https?://)?(www\.)?(tiktok\.com)',
        r'(https?://)?(www\.)?(instagram\.com)',
        r'(https?://)?(www\.)?(twitter\.com|x\.com)',
        r'(https?://)?(www\.)?(facebook\.com)',
    ]
    return any(re.search(pattern, url) for pattern in patterns)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)

    stats = db.get_user_stats(user.id)

    premium_status = ""
    if stats['is_premium']:
        premium_status = "\n\n💎 У вас активен премиум!"
    else:
        premium_status = f"\n\n📊 Скачиваний сегодня: {stats['downloads_today']}/3"

    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот для скачивания видео из социальных сетей!\n\n"
        "Поддерживаю:\n"
        "✅ YouTube\n"
        "✅ TikTok\n"
        "✅ Instagram\n"
        "✅ Twitter/X\n"
        "✅ Facebook\n\n"
        "Просто отправь мне ссылку на видео!\n\n"
        f"{premium_status}\n\n"
        "Команды:\n"
        "/start - начать работу\n"
        "/help - помощь\n"
        "/premium - купить премиум\n"
        "/stats - моя статистика"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Как использовать бота:\n\n"
        "1. Скопируйте ссылку на видео\n"
        "2. Отправьте её мне\n"
        "3. Подождите немного\n"
        "4. Получите видео!\n\n"
        "Поддерживаемые платформы:\n"
        "• YouTube\n"
        "• TikTok\n"
        "• Instagram\n"
        "• Twitter/X\n"
        "• Facebook\n\n"
        "🆓 Бесплатно: 3 видео в день\n"
        "💎 Премиум: безлимит за 100₽/месяц"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика пользователя"""
    user = update.effective_user
    stats = db.get_user_stats(user.id)

    if not stats:
        await update.message.reply_text("Ошибка получения статистики")
        return

    status = "💎 Премиум" if stats['is_premium'] else "🆓 Бесплатный"

    if user.id in ADMIN_IDS:
        status = "👑 Администратор"

    await update.message.reply_text(
        f"📊 Ваша статистика:\n\n"
        f"Статус: {status}\n"
        f"Скачиваний сегодня: {stats['downloads_today']}/{'∞' if user.id in ADMIN_IDS else '3'}\n"
        f"Всего скачано: {stats['total_downloads']}\n\n"
        f"Хотите безлимит? /premium"
    )

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать свой Telegram ID"""
    user = update.effective_user
    await update.message.reply_text(
        f"Ваш Telegram ID: `{user.id}`\n\n"
        f"Username: @{user.username or 'не установлен'}\n"
        f"Имя: {user.first_name}",
        parse_mode='Markdown'
    )

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка премиума"""
    user = update.effective_user
    stats = db.get_user_stats(user.id)

    if stats['is_premium']:
        await update.message.reply_text(
            "💎 У вас уже активен премиум!\n\n"
            f"Действует до: {stats['premium_until'][:10]}"
        )
        return

    keyboard = [
        [InlineKeyboardButton("💎 Купить премиум (100₽/месяц)", callback_data="buy_premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💎 Премиум подписка\n\n"
        "Что вы получите:\n"
        "✅ Безлимитные скачивания\n"
        "✅ Приоритетная обработка\n"
        "✅ Без рекламы\n\n"
        "Цена: 100₽ за месяц\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "buy_premium":
        user = query.from_user

        try:
            payment = create_payment(
                user.id,
                PREMIUM_MONTH_PRICE,
                f"Премиум подписка на 1 месяц для @{user.username or user.first_name}"
            )

            db.add_payment(user.id, PREMIUM_MONTH_PRICE, payment.id, "pending")

            keyboard = [
                [InlineKeyboardButton("💳 Оплатить", url=payment.confirmation.confirmation_url)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "💳 Счет создан!\n\n"
                f"Сумма: {PREMIUM_MONTH_PRICE}₽\n\n"
                "Нажмите кнопку ниже для оплаты.\n"
                "После оплаты напишите /start чтобы проверить статус.",
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            await query.edit_message_text(
                "❌ Ошибка создания платежа.\n\n"
                "Платежная система временно недоступна.\n"
                "Попробуйте позже или свяжитесь с поддержкой."
            )

async def download_video(url):
    """Скачивание видео по ссылке"""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'Видео')
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None, None

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ссылок на видео"""
    user = update.effective_user
    url = update.message.text.strip()

    if not is_valid_url(url):
        await update.message.reply_text(
            "Это не похоже на ссылку на видео 🤔\n\n"
            "Отправьте ссылку с YouTube, TikTok, Instagram, Twitter или Facebook"
        )
        return

    # Проверяем лимиты (администраторы пропускают проверку)
    if user.id not in ADMIN_IDS:
        can_download, message = db.can_download(user.id)

        if not can_download:
            keyboard = [
                [InlineKeyboardButton("💎 Купить премиум", callback_data="buy_premium")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"❌ {message}",
                reply_markup=reply_markup
            )
            return

    status_msg = await update.message.reply_text("⏳ Скачиваю видео...")

    try:
        filename, title = await download_video(url)

        if filename and os.path.exists(filename):
            file_size = os.path.getsize(filename)

            if file_size > 50 * 1024 * 1024:
                await status_msg.edit_text(
                    "❌ Видео слишком большое (больше 50 МБ).\n"
                    "Telegram не позволяет отправлять такие большие файлы."
                )
                os.remove(filename)
                return

            await status_msg.edit_text("📤 Отправляю видео...")

            with open(filename, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption=f"✅ {title}",
                    supports_streaming=True
                )

            # Увеличиваем счетчик скачиваний
            db.increment_download(user.id)

            await status_msg.delete()
            os.remove(filename)

            # Показываем оставшиеся скачивания (не для админов)
            if user.id not in ADMIN_IDS:
                stats = db.get_user_stats(user.id)
                if not stats['is_premium'] and stats['downloads_today'] >= 3:
                    keyboard = [
                        [InlineKeyboardButton("💎 Купить премиум", callback_data="buy_premium")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.message.reply_text(
                        "⚠️ Вы использовали все бесплатные скачивания на сегодня!\n\n"
                        "Купите премиум для безлимитных скачиваний:",
                        reply_markup=reply_markup
                    )

        else:
            await status_msg.edit_text(
                "❌ Не удалось скачать видео.\n"
                "Возможно, видео приватное или ссылка неверная."
            )

    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        await status_msg.edit_text(
            "❌ Произошла ошибка при скачивании.\n"
            "Попробуйте другую ссылку или повторите позже."
        )

def main():
    """Запуск бота"""
    logger.info("Запуск бота для скачивания видео...")

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("myid", myid_command))

    # Регистрируем обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

    # Регистрируем обработчик ссылок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
