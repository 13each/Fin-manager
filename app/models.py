import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            categories TEXT DEFAULT '{}'
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
    cursor.execute('UPDATE users SET categories = ? WHERE email = ?', (json.dumps(categories), email))
    conn.commit()
    conn.close()


def get_categories(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT categories FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else {}
