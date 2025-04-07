import psycopg2
import os
import json
import datetime
import copy
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    confirmed BOOLEAN DEFAULT FALSE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spending (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                    current_categories JSONB DEFAULT '{}'::jsonb,
                    monthly_history JSONB DEFAULT '[]'::jsonb
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accumulation (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    goal_name TEXT NOT NULL,
                    accumulated REAL DEFAULT 0,
                    total REAL NOT NULL
                )
            ''')


def get_user_by_email(email):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            return cursor.fetchone()


def update_categories(email, categories):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            row = cursor.fetchone()
            if not row:
                return
            user_id = row["id"]
            cursor.execute(
                'UPDATE spending SET current_categories = %s WHERE user_id = %s',
                (json.dumps(categories), user_id)
            )


def get_categories(email):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            row = cursor.fetchone()
            if not row:
                return {}
            user_id = row["id"]
            cursor.execute('SELECT current_categories FROM spending WHERE user_id = %s', (user_id,))
            row = cursor.fetchone()
            return row["current_categories"] if row and row["current_categories"] else {}


def confirm_user_email(email):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('UPDATE users SET confirmed = TRUE WHERE email = %s', (email,))


def update_user_password(email, new_hashed_password):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'UPDATE users SET password = %s WHERE email = %s',
                (new_hashed_password, email)
            )


def archive_monthly_spending():
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id, current_categories, monthly_history FROM spending')
            records = cursor.fetchall()

            for rec in records:
                spending_id = rec["id"]
                current_categories = rec["current_categories"] or {}
                monthly_history = rec["monthly_history"] or []

                snapshot = {
                    "year": year,
                    "month": month,
                    "categories": copy.deepcopy(current_categories)
                }

                monthly_history.append(snapshot)
                if len(monthly_history) > 12:
                    monthly_history = monthly_history[-12:]

                for cat in current_categories:
                    current_categories[cat]["spent"] = 0

                cursor.execute(
                    'UPDATE spending SET current_categories = %s, monthly_history = %s WHERE id = %s',
                    (json.dumps(current_categories), json.dumps(monthly_history), spending_id)
                )


def get_monthly_history(email):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            row = cursor.fetchone()
            if not row:
                return []
            user_id = row["id"]
            cursor.execute('SELECT monthly_history FROM spending WHERE user_id = %s', (user_id,))
            row = cursor.fetchone()
            return row["monthly_history"] if row and row["monthly_history"] else []


def get_accumulation(user_email):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT * FROM accumulation WHERE user_id = (SELECT id FROM users WHERE email = %s)',
                (user_email,)
            )
            return cursor.fetchone()


def add_accumulation(user_email, goal_name, total):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id FROM users WHERE email = %s', (user_email,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row["id"]
                cursor.execute(
                    'INSERT INTO accumulation (user_id, goal_name, total) VALUES (%s, %s, %s)',
                    (user_id, goal_name, total)
                )
