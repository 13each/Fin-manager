import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import get_user_by_email, update_categories, get_categories
import bcrypt
import json

routes = Blueprint('routes', __name__)


@routes.route('/')
def home():
    if 'user_email' in session:
        return f"Hello, {session['user_email']}! Welcome to Fin Manager."
    return "Hello, Fin Manager! Please log in or register."


@routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match!", 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            conn = sqlite3.connect('app/database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return "Email already exists!", 400

        return redirect(url_for('routes.login'))

    return render_template('register.html')


@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)
        if not user:
            return "User not found!", 404

        hashed_password = user[2]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            session['user_email'] = email
            return redirect(url_for('routes.home'))
        else:
            return "Invalid password!", 401

    return render_template('login.html')


@routes.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('routes.home'))


@routes.route('/add-category', methods=['GET', 'POST'])
def add_category():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    if request.method == 'POST':
        name = request.form['name']
        limit = float(request.form['limit'])

        categories = get_categories(session['user_email'])

        if name in categories:
            return f"Category '{name}' already exists!", 400

        categories[name] = {"limit": limit, "spent": 0}
        update_categories(session['user_email'], categories)

        return redirect(url_for('routes.home'))

    return render_template('add_category.html')


@routes.route('/add-spending', methods=['GET', 'POST'])
def add_spending():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    categories = get_categories(session['user_email'])

    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])

        if category not in categories:
            return f"Category '{category}' does not exist!", 400

        categories[category]['spent'] += amount
        update_categories(session['user_email'], categories)

        return redirect(url_for('routes.home'))

    return render_template('add_spending.html', categories=categories)
