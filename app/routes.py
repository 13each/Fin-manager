import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models import (get_user_by_email, update_categories, get_categories, update_user_password,
                        get_monthly_history, archive_monthly_spending, DB_PATH)
import bcrypt
import random
from flask_mail import Message
from app import mail

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
            flash("Passwords do not match!", "error")
            return redirect(url_for('routes.register'))

        if get_user_by_email(email):
            flash("Email already exists!", "error")
            return redirect(url_for('routes.register'))

        confirmation_code = str(random.randint(100000, 999999))

        msg = Message("Confirm your email", recipients=[email])
        msg.body = f"Your confirmation code: {confirmation_code}"
        mail.send(msg)

        session['pending_registration'] = {
            'email': email,
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'code': confirmation_code
        }

        flash("A confirmation code has been sent to your email.", "info")
        return redirect(url_for('routes.confirm_email'))

    return render_template('register.html')


@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            flash("Invalid mail or password", "error")
            return redirect(url_for('routes.login'))

        if user[3] == 0:
            flash("Your email is not confirmed. Please check your email.", "error")
            return redirect(url_for('routes.login'))

        session['user_email'] = email
        return redirect(url_for('routes.home'))

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
        try:
            limit = float(request.form['limit'])
        except ValueError:
            flash("Invalid limit value!", "error")
            return redirect(url_for('routes.add_category'))
        categories = get_categories(session['user_email'])

        if name in categories:
            flash(f"Category {name} already exists!", "error")
            return redirect(url_for('routes.add_category'))

        categories[name] = {"limit": limit, "spent": 0}
        update_categories(session['user_email'], categories)
        flash("Category added successfully", "success")
        return redirect(url_for('routes.add_category'))

    return render_template('add_category.html')


@routes.route('/add-spending', methods=['GET', 'POST'])
def add_spending():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    categories = get_categories(session['user_email'])
    if request.method == 'POST':
        category = request.form['category']
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash("Invalid amount value", "error")
            return redirect(url_for('routes.add_spending'))

        if amount < 0:
            flash("Spending amount cannot be negative", "error")
            return redirect(url_for('routes.add_spending'))

        if category not in categories:
            flash(f"Category {category} does not exist!", "error")
            return redirect(url_for('routes.add_spending'))

        session['last_spending'] = {'category': category, 'amount': amount}

        categories[category]['spent'] += amount
        update_categories(session['user_email'], categories)
        flash("Spending added successfully", "success")
        return redirect(url_for('routes.add_spending'))

    return render_template('add_spending.html', categories=categories)


@routes.route('/spending-chart')
def spending_chart():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    categories_data = get_categories(session['user_email'])

    data = []
    bgColors = []
    categoryLabels = []

    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FFA07A', '#8A2BE2']

    for i, (cat, catData) in enumerate(categories_data.items()):
        limit = catData.get("limit", 0)
        spent = catData.get("spent", 0)
        if limit <= 0:
            continue
        if spent > limit:
            spent = limit
        remaining = limit - spent

        data.append(spent)
        data.append(remaining)

        color = colors[i % len(colors)]
        bgColors.append(color)
        bgColors.append('#e0e0e0')

        categoryLabels.append(cat)

    chart_data = {
        "data": data,
        "backgroundColors": bgColors,
        "categoryLabels": categoryLabels
    }

    return render_template('spending_chart.html', chart_data=chart_data)


@routes.route('/history')
def history():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))
    history_data = get_monthly_history(session['user_email'])
    return render_template('history.html', history=history_data)


@routes.route('/undo-spending-ajax', methods=['POST'])
def undo_spending_ajax():
    if 'user_email' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 403

    last_spending = session.get('last_spending')
    if not last_spending:
        return jsonify({"status": "error", "message": "No spending to undo"}), 400

    category = last_spending.get('category')
    amount = last_spending.get('amount', 0)
    categories = get_categories(session['user_email'])

    if category in categories:
        categories[category]['spent'] = max(categories[category]['spent'] - amount, 0)
        update_categories(session['user_email'], categories)
        session.pop('last_spending', None)
        return jsonify({"status": "success", "message": "Last spending undone successfully"})
    else:
        return jsonify({"status": "error", "message": "Category not found, cannot undo"}), 400


@routes.route('/confirm-email', methods=['GET', 'POST'])
def confirm_email():
    if request.method == 'POST':
        entered_code = request.form['code']
        pending_data = session.get('pending_registration')

        if not pending_data:
            flash("No registration data found. Please register again.", "error")
            return redirect(url_for('routes.register'))

        if entered_code == pending_data['code']:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (email, password, confirmed) VALUES (?, ?, 1)',
                           (pending_data['email'], pending_data['password']))
            user_id = cursor.lastrowid
            cursor.execute('INSERT INTO spending (user_id, current_categories, monthly_history) VALUES (?, ?, ?)',
                           (user_id, '{}', '[]'))
            conn.commit()
            conn.close()

            session.pop('pending_registration', None)

            flash("Your email has been confirmed. You can now log in!", "success")
            return redirect(url_for('routes.login'))
        else:
            flash("Invalid confirmation code!", "error")

    return render_template('confirm_email.html')


@routes.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        if not user:
            flash("No user found with that email.", "error")
            return redirect(url_for('routes.reset_password_request'))

        reset_code = str(random.randint(100000, 999999))

        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Your password reset code is: {reset_code}"
        mail.send(msg)

        session['password_reset'] = {
            'email': email,
            'code': reset_code
        }
        flash("A password reset code has been sent to your email.", "info")
        return redirect(url_for('routes.reset_password'))
    return render_template('reset_password_request.html')


@routes.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        entered_code = request.form['code']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('routes.reset_password'))

        reset_data = session.get('password_reset')
        if not reset_data:
            flash("Reset data not found. Please request a new code.", "error")
            return redirect(url_for('routes.reset_password_request'))

        if entered_code != reset_data['code']:
            flash("Invalid reset code. Please try again.", "error")
            return redirect(url_for('routes.reset_password'))

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_user_password(reset_data['email'], hashed_password)

        session.pop('password_reset', None)

        flash("Password successfully updated. You can now log in.", "success")
        return redirect(url_for('routes.login'))

    return render_template('reset_password.html')
