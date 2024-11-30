# database.py
import sqlite3
import time

class Database:
    def __init__(self, db_path='bot.db'):
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        with self.connection:
            # Таблица пользователей
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    referrer_id INTEGER,
                    balance REAL DEFAULT 0,
                    invited_count INTEGER DEFAULT 0,
                    daily_clicks INTEGER DEFAULT 0,
                    last_click_time INTEGER DEFAULT 0
                )
            """)
            # Таблица запросов на вывод
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS withdraw_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    status TEXT DEFAULT 'processing'
                )
            """)
            # Таблица билетов лотереи
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS lottery_tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT
                )
            """)
            # Таблица логов игр
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    bet_amount REAL,
                    user_dice INTEGER,
                    bot_dice INTEGER,
                    result TEXT
                )
            """)
            # Таблица рефералов
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    user_id INTEGER PRIMARY KEY,
                    referrer_id INTEGER,
                    referral_income REAL DEFAULT 0
                )
            """)

    # Методы для пользователей
    def add_user(self, user_id, username, referrer_id=None):
        with self.connection:
            self.cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, username, referrer_id)
                VALUES (?, ?, ?)
            """, (user_id, username, referrer_id))
            if referrer_id:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO referrals (user_id, referrer_id)
                    VALUES (?, ?)
                """, (user_id, referrer_id))

    def get_user(self, user_id):
        with self.connection:
            return self.cursor.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()

    def update_balance(self, user_id, amount):
        with self.connection:
            self.cursor.execute("""
                UPDATE users SET balance = balance + ? WHERE user_id = ?
            """, (amount, user_id))

    def increment_invited(self, user_id):
        with self.connection:
            self.cursor.execute("""
                UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?
            """, (user_id,))

    def add_game_log(self, user_id, bet_amount, user_dice, bot_dice, result):
        with self.connection:
            self.cursor.execute("""
                INSERT INTO game_logs (user_id, bet_amount, user_dice, bot_dice, result)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, bet_amount, user_dice, bot_dice, result))

    def update_referral_income(self, referrer_id, amount):
        with self.connection:
            self.cursor.execute("""
                UPDATE referrals SET referral_income = referral_income + ? WHERE user_id = ?
            """, (amount, referrer_id))

    # Методы для лотереи
    def add_lottery_ticket(self, user_id, date):
        with self.connection:
            self.cursor.execute("""
                INSERT INTO lottery_tickets (user_id, date) VALUES (?, ?)
            """, (user_id, date))

    def get_lottery_tickets(self, date):
        with self.connection:
            return self.cursor.execute("""
                SELECT user_id FROM lottery_tickets WHERE date = ?
            """, (date,)).fetchall()

    def clear_lottery_tickets(self, date):
        with self.connection:
            self.cursor.execute("""
                DELETE FROM lottery_tickets WHERE date = ?
            """, (date,))

    # Методы для запросов на вывод
    def add_withdraw_request(self, user_id, amount):
        with self.connection:
            self.cursor.execute("""
                INSERT INTO withdraw_requests (user_id, amount) VALUES (?, ?)
            """, (user_id, amount))

    def get_withdraw_requests(self):
        with self.connection:
            return self.cursor.execute("""
                SELECT * FROM withdraw_requests WHERE status = 'processing'
            """).fetchall()

    def update_withdraw_status(self, request_id, status):
        with self.connection:
            self.cursor.execute("""
                UPDATE withdraw_requests SET status = ? WHERE id = ?
            """, (status, request_id))

    # Методы для мини-игры (кликалки)
    def reset_daily_clicks(self):
        with self.connection:
            self.cursor.execute("""
                UPDATE users SET daily_clicks = 0
            """)

    def update_last_click_time(self, user_id, timestamp):
        with self.connection:
            self.cursor.execute("""
                UPDATE users SET last_click_time = ? WHERE user_id = ?
            """, (timestamp, user_id))

    def increment_daily_clicks(self, user_id):
        with self.connection:
            self.cursor.execute("""
                UPDATE users SET daily_clicks = daily_clicks + 1 WHERE user_id = ?
            """, (user_id,))

    # Общие методы
    def get_total_users(self):
        with self.connection:
            return self.cursor.execute("""
                SELECT COUNT(*) FROM users
            """).fetchone()[0]

    def get_all_users(self):
        with self.connection:
            return self.cursor.execute("""
                SELECT user_id FROM users
            """).fetchall()
