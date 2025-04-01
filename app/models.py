import sqlite3
import os
import json
import datetime
import copy

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            confirmed INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            current_categories TEXT DEFAULT '{}',
            monthly_history TEXT DEFAULT '[]',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS accumulation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_name TEXT NOT NULL,
                accumulated REAL DEFAULT 0,
                total REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def update_categories(email, categories):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    user_id = row[0]
    cursor.execute('UPDATE spending SET current_categories = ? WHERE user_id = ?',
                   (json.dumps(categories), user_id))
    conn.commit()
    conn.close()


def get_categories(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {}
    user_id = row[0]
    cursor.execute("SELECT current_categories FROM spending WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else {}


def confirm_user_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET confirmed = 1 WHERE email = ?', (email,))
    conn.commit()
    conn.close()


def update_user_password(email, new_hashed_password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (new_hashed_password, email))
    conn.commit()
    conn.close()


def archive_monthly_spending():
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, current_categories, monthly_history FROM spending")
    records = cursor.fetchall()

    for rec in records:
        spending_id, current_json, history_json = rec
        current_categories = json.loads(current_json) if current_json else {}
        monthly_history = json.loads(history_json) if history_json else []

        snapshot = {
            "year": year,
            "month": month,
            "categories": copy.deepcopy(current_categories)
        }
        monthly_history.append(snapshot)
        if len(monthly_history) > 12:
            monthly_history = monthly_history[-12:]

        for cat, data in current_categories.items():
            data["spent"] = 0

        cursor.execute(
            "UPDATE spending SET current_categories = ?, monthly_history = ? WHERE id = ?",
            (json.dumps(current_categories), json.dumps(monthly_history), spending_id)
        )

    conn.commit()
    conn.close()


def get_monthly_history(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return []
    user_id = row[0]
    cursor.execute("SELECT monthly_history FROM spending WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else []


def get_accumulation(user_email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM accumulation WHERE user_id = (SELECT id FROM users WHERE email = ?)', (user_email,))
    row = cursor.fetchone()
    conn.close()
    return row


def add_accumulation(user_email, goal_name, total):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cursor.fetchone()
    if user_row:
        user_id = user_row[0]
        cursor.execute("INSERT INTO accumulation (user_id, goal_name, total) VALUES (?, ?, ?)",
                       (user_id, goal_name, total))
        conn.commit()
    conn.close()
