import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models import get_user_by_email, update_categories, get_categories
import bcrypt

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

    categories = get_categories(session['user_email'])
    return render_template('history.html', categories=categories)



@routes.route('/undo-spending-ajax', methods = ['POST'])
def undo_spending_ajax():
    if 'user_email' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 403

    last_spending = session['last_spending']
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