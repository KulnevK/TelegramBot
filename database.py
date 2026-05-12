import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_file='bot_users.db'):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                downloads_today INTEGER DEFAULT 0,
                last_download_date TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                total_downloads INTEGER DEFAULT 0,
                registration_date TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                payment_id TEXT,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        conn.commit()
        conn.close()

    def get_user(self, user_id):
        """Получить данные пользователя"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        conn.close()
        return user

    def add_user(self, user_id, username, first_name):
        """Добавить нового пользователя"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, registration_date, last_download_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, now, now))

        conn.commit()
        conn.close()

    def can_download(self, user_id):
        """Проверить, может ли пользователь скачать видео"""
        user = self.get_user(user_id)

        if not user:
            return False, "Пользователь не найден"

        # Проверяем премиум
        if user[5] == 1:  # is_premium
            premium_until = datetime.fromisoformat(user[6])
            if datetime.now() < premium_until:
                return True, "premium"

        # Проверяем бесплатный лимит
        today = datetime.now().date().isoformat()
        last_download = user[4]  # last_download_date

        if last_download:
            last_date = datetime.fromisoformat(last_download).date().isoformat()
            if last_date != today:
                # Новый день - сбрасываем счетчик
                self.reset_daily_downloads(user_id)
                return True, "free"

        downloads_today = user[3]  # downloads_today

        if downloads_today < 3:
            return True, "free"

        return False, f"Вы использовали все 3 бесплатных скачивания сегодня.\n\n💎 Купите премиум для безлимитных скачиваний!"

    def increment_download(self, user_id):
        """Увеличить счетчик скачиваний"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
            UPDATE users
            SET downloads_today = downloads_today + 1,
                total_downloads = total_downloads + 1,
                last_download_date = ?
            WHERE user_id = ?
        ''', (now, user_id))

        conn.commit()
        conn.close()

    def reset_daily_downloads(self, user_id):
        """Сбросить дневной счетчик"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET downloads_today = 0
            WHERE user_id = ?
        ''', (user_id,))

        conn.commit()
        conn.close()

    def activate_premium(self, user_id, days=30):
        """Активировать премиум"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        premium_until = (datetime.now() + timedelta(days=days)).isoformat()

        cursor.execute('''
            UPDATE users
            SET is_premium = 1,
                premium_until = ?
            WHERE user_id = ?
        ''', (premium_until, user_id))

        conn.commit()
        conn.close()

    def add_payment(self, user_id, amount, payment_id, status):
        """Добавить запись о платеже"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO payments (user_id, amount, payment_id, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, payment_id, status, now))

        conn.commit()
        conn.close()

    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        user = self.get_user(user_id)

        if not user:
            return None

        stats = {
            'downloads_today': user[3],
            'total_downloads': user[7],
            'is_premium': user[5] == 1,
            'premium_until': user[6] if user[5] == 1 else None
        }

        return stats
