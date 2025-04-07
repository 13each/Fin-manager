import psycopg2
import bcrypt
import random
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from flask_mail import Message

from app import mail
from app.models import (
    get_user_by_email, update_categories, get_categories,
    update_user_password, get_monthly_history,
    add_accumulation, get_accumulation, get_connection
)

routes = Blueprint('routes', __name__)


@routes.route('/')
def home():
    if 'user_email' in session:
        categories = get_categories(session['user_email'])
        if not categories:
            return redirect(url_for('routes.view_categories'))
        return render_template('spending_chart.html', categories=categories)

    return render_template('login.html')


@routes.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_email' in session:
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            if session.get('lang') == 'ru':
                flash("Пароли не совпадают", "error")
            else:
                flash("Passwords do not match!", "error")
            return redirect(url_for('routes.register'))

        if get_user_by_email(email):
            if session.get('lang') == 'ru':
                flash("Аккаунт с данной почтой уже зарегестрирован", "error")
            else:
                flash("Email already exists!", "error")
            return redirect(url_for('routes.register'))

        confirmation_code = str(random.randint(100000, 999999))

        if session.get('lang') == 'ru':
            msg = Message("Подтверждение почты", recipients=[email])
            msg.body = f"Ваш код подтверждения: {confirmation_code}"
        else:
            msg = Message("Confirm your email", recipients=[email])
            msg.body = f"Your confirmation code: {confirmation_code}"
        mail.send(msg)

        session['pending_registration'] = {
            'email': email,
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'code': confirmation_code
        }

        if session.get('lang') == 'ru':
            flash("Код подтверждения был выслан на ваш email.", "info")
        else:
            flash("A confirmation code has been sent to your email.", "info")

        return redirect(url_for('routes.confirm_email'))

    return render_template('register.html')


@routes.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            if session.get('lang') == 'ru':
                flash("Неверный email или пароль", "error")
            else:
                flash("Invalid email or password", "error")
            return redirect(url_for('routes.login'))

        if user[3] == 0:
            if session.get('lang') == 'ru':
                flash("Ваш email не подтвержден. Пожалуйста, проверьте почту.", "error")
            else:
                flash("Your email is not confirmed. Please check your email.", "error")
            return redirect(url_for('routes.login'))

        session['user_email'] = email
        return redirect(url_for('routes.home'))

    return render_template('login.html')


@routes.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('routes.home'))


@routes.route('/add-category', methods=['POST'])
def add_category():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    name = request.form['name']
    try:
        limit = float(request.form['limit'])
        if limit < 0:
            return "Limit must be non-negative", 400
    except ValueError:
        return "Invalid limit", 400

    color_input = request.form.get('color') or "#000000"
    categories = get_categories(session['user_email'])

    if name in categories:
        return "Category already exists", 400

    categories[name] = {
        "limit": limit,
        "spent": 0,
        "color": color_input
    }
    update_categories(session['user_email'], categories)
    return redirect(url_for('routes.view_categories'))


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
            return redirect(url_for('routes.home'))

        if amount < 0:
            return redirect(url_for('routes.home'))

        if category not in categories:
            return redirect(url_for('routes.home'))

        session['last_spending'] = {
            'category': category,
            'amount': amount
        }
        categories[category]['spent'] += amount
        update_categories(session['user_email'], categories)

        if session.get('lang') == 'ru':
            flash("Трата успешно добавлена", "success")
        else:
            flash("Spending added successfully", "success")

        return redirect(url_for('routes.home'))

    return redirect(url_for('routes.home'))


@routes.route('/history')
def history():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    history_data = get_monthly_history(session['user_email'])
    summary_list = []

    for snapshot in history_data:
        year = snapshot.get("year")
        month = snapshot.get("month")
        categories = snapshot.get("categories", {})
        total_spent = 0
        total_limit = 0

        for cat, data in categories.items():
            total_spent += data.get("spent", 0)
            total_limit += data.get("limit", 0)

        summary_list.append({
            "year": year,
            "month": month,
            "total_spent": total_spent,
            "total_limit": total_limit
        })

    summary_list.sort(key=lambda x: (x["year"], x["month"]), reverse=True)

    return render_template('history.html', summaries=summary_list)


@routes.route('/history/<int:year>/<int:month>')
def history_detail(year, month):
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    history_data = get_monthly_history(session['user_email'])
    snapshot = next(
        (s for s in history_data if s.get("year") == year and s.get("month") == month),
        None
    )

    if not snapshot:
        return redirect(url_for('routes.history'))

    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
              '#9966FF', '#FFA07A', '#8A2BE2']
    categories = snapshot.get("categories", {})
    category_list = []

    for cat, cat_data in categories.items():
        limit = cat_data.get("limit", 0)
        if limit <= 0:
            continue
        spent = cat_data.get("spent", 0)
        category_list.append({
            'category': cat,
            'spent': spent,
            'limit': limit,
            'color': colors[len(category_list) % len(colors)]
        })

    category_list.sort(key=lambda item: item['spent'] / item['limit'])

    interleaved = []
    left, right = 0, len(category_list) - 1
    while left <= right:
        if left == right:
            interleaved.append(category_list[left])
        else:
            interleaved.append(category_list[left])
            interleaved.append(category_list[right])
        left += 1
        right -= 1

    data = []
    bg_colors = []
    category_labels = []
    legend_data = []

    for item in interleaved:
        cat = item['category']
        actual_spent = item['spent']
        limit = item['limit']
        clamped_spent = min(actual_spent, limit)
        allocated = limit - clamped_spent
        data.extend([clamped_spent, allocated])
        bg_colors.extend([item['color'], '#e0e0e0'])
        category_labels.append(cat)
        legend_data.append({
            'category': cat,
            'spent': actual_spent,
            'limit': limit,
            'color': item['color']
        })

    chart_data = {
        "data": data,
        "backgroundColors": bg_colors,
        "categoryLabels": category_labels,
        "legend": legend_data
    }

    return render_template(
        'history_chart.html',
        chart_data=chart_data,
        year=year,
        month=month
    )


@routes.route('/undo-spending-ajax', methods=['POST'])
def undo_spending_ajax():
    if 'user_email' not in session:
        return jsonify({
            "status": "error",
            "message": "Not logged in"
        }), 403

    last_spending = session.get('last_spending')
    if not last_spending:
        return jsonify({
            "status": "error",
            "message": "No spending to undo"
        }), 400

    category = last_spending.get('category')
    amount = last_spending.get('amount', 0)
    categories = get_categories(session['user_email'])

    if category in categories:
        categories[category]['spent'] = max(
            categories[category]['spent'] - amount, 0
        )
        update_categories(session['user_email'], categories)
        session.pop('last_spending', None)
        return jsonify({
            "status": "success",
            "message": "Last spending undone successfully"
        })

    return jsonify({
        "status": "error",
        "message": "Category not found, cannot undo"
    }), 400


@routes.route('/confirm-email', methods=['GET', 'POST'])
def confirm_email():
    if request.method == 'POST':
        entered_code = request.form['code']
        pending_data = session.get('pending_registration')

        if not pending_data:
            msg = "Данный email не найден. Пожалуйста, попробуйте ещё раз." if session.get(
                'lang') == 'ru' else "No registration data found. Please register again."
            flash(msg, "error")
            return redirect(url_for('routes.register'))

        if entered_code == pending_data['code']:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'INSERT INTO users (email, password, confirmed) VALUES (%s, %s, %s) RETURNING id',
                (pending_data['email'], pending_data['password'], True)
            )
            user_id = cursor.fetchone()[0]

            cursor.execute(
                'INSERT INTO spending (user_id, current_categories, monthly_history) VALUES (%s, %s, %s)',
                (user_id, '{}', '[]')
            )
            conn.commit()
            conn.close()

            session.pop('pending_registration', None)
            return redirect(url_for('routes.login'))
        else:
            msg = "Неверный код подтверждения!" if session.get('lang') == 'ru' else "Invalid confirmation code!"
            flash(msg, "error")

    return render_template('confirm_email.html')


@routes.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if 'user_email' in session:
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)

        if not user:
            if session.get('lang') == 'ru':
                flash("Не найден пользователь с такой почтой.", "error")
            else:
                flash("No user found with that email.", "error")
            return redirect(url_for('routes.reset_password_request'))

        reset_code = str(random.randint(100000, 999999))

        if session.get('lang') == 'ru':
            msg = Message("Сброс пароля", recipients=[email])
            msg.body = f"Ваш код для сброса пароля: {reset_code}"
        else:
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Your password reset code is: {reset_code}"
        mail.send(msg)

        session['password_reset'] = {
            'email': email,
            'code': reset_code
        }

        if session.get('lang') == 'ru':
            flash("Код подтверждения был выслан на вашу почту.", "info")
        else:
            flash("A password reset code has been sent to your email.", "info")

        return redirect(url_for('routes.reset_password'))

    return render_template('reset_password_request.html')


@routes.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'user_email' in session:
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        entered_code = request.form['code']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            if session.get('lang') == 'ru':
                flash("Пароли не совпадают!", "error")
            else:
                flash("Passwords do not match!", "error")
            return redirect(url_for('routes.reset_password'))

        reset_data = session.get('password_reset')
        if not reset_data:
            if session.get('lang') == 'ru':
                flash("Данные о сбросе пароля не найдены. Пожалуйста, попробуйте ещё раз.", "error")
            else:
                flash("Reset data not found. Please request a new code.", "error")
            return redirect(url_for('routes.reset_password_request'))

        if entered_code != reset_data['code']:
            if session.get('lang') == 'ru':
                flash("Неверный код сброса. Пожалуйста, попробуйте ещё раз.", "error")
            else:
                flash("Invalid reset code. Please try again.", "error")
            return redirect(url_for('routes.reset_password'))

        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        update_user_password(reset_data['email'], hashed_password)
        session.pop('password_reset', None)

        return redirect(url_for('routes.login'))

    return render_template('reset_password.html')


@routes.route('/categories', methods=['GET'])
def view_categories():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    user_categories = get_categories(session['user_email'])

    return render_template('categories.html', categories=user_categories)


@routes.route('/update-category', methods=['POST'])
def update_category():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')

    try:
        new_limit = float(request.form.get('new_limit'))
    except ValueError:
        return redirect(url_for('routes.view_categories'))

    new_color = request.form.get('new_color') or "#000000"

    user_categories = get_categories(session['user_email'])

    if old_name not in user_categories:
        return redirect(url_for('routes.view_categories'))

    if new_name != old_name:
        if new_name in user_categories:
            return redirect(url_for('routes.view_categories'))

        cat_data = user_categories.pop(old_name)
        cat_data['limit'] = new_limit
        cat_data['color'] = new_color
        user_categories[new_name] = cat_data
    else:
        user_categories[old_name]['limit'] = new_limit
        user_categories[old_name]['color'] = new_color

    update_categories(session['user_email'], user_categories)

    return redirect(url_for('routes.view_categories'))


@routes.route('/delete-category', methods=['POST'])
def delete_category():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    category_name = request.form.get('category_name')
    user_categories = get_categories(session['user_email'])

    if category_name in user_categories:
        user_categories.pop(category_name)
        update_categories(session['user_email'], user_categories)

    return redirect(url_for('routes.view_categories'))


@routes.route('/accumulation', methods=['GET', 'POST'])
def accumulation():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    if request.method == 'POST':
        goal_name = request.form['goal_name']

        try:
            total = float(request.form['total'])
        except ValueError:
            return redirect(url_for('routes.accumulation'))

        add_accumulation(session['user_email'], goal_name, total)

        return redirect(url_for('routes.accumulation'))

    accumulation_goal = get_accumulation(session['user_email'])

    return render_template('accumulation.html', accumulation=accumulation_goal)


@routes.route('/add_money', methods=['POST'])
def add_money():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    try:
        amount = float(request.form['amount'])
    except ValueError:
        return redirect(url_for('routes.accumulation'))

    if amount < 0:
        return redirect(url_for('routes.accumulation'))

    accum = get_accumulation(session['user_email'])
    if not accum:
        return redirect(url_for('routes.accumulation'))

    accum_id, _, _, current_accumulated, total = accum
    new_accumulated = min(current_accumulated + amount, total)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE accumulation SET accumulated = %s WHERE id = %s',
        (new_accumulated, accum_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('routes.accumulation'))


@routes.route('/update_goal', methods=['POST'])
def update_goal():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    new_goal_name = request.form.get('new_goal_name')

    try:
        new_total = float(request.form.get('new_total'))
    except (ValueError, TypeError):
        return redirect(url_for('routes.accumulation'))

    accum = get_accumulation(session['user_email'])
    if not accum:
        return redirect(url_for('routes.accumulation'))

    accum_id = accum[0]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE accumulation SET goal_name = %s, total = %s WHERE id = %s',
        (new_goal_name, new_total, accum_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('routes.accumulation'))


@routes.route('/delete_goal', methods=['POST'])
def delete_goal():
    if 'user_email' not in session:
        return redirect(url_for('routes.login'))

    accum = get_accumulation(session['user_email'])
    if accum:
        accum_id = accum[0]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accumulation WHERE id = %s', (accum_id,))
        conn.commit()
        conn.close()

    return redirect(url_for('routes.accumulation'))


@routes.route('/switch_language')
def switch_language():
    current_lang = session.get('lang', 'en')
    session['lang'] = 'ru' if current_lang == 'en' else 'en'
    return redirect(request.referrer or url_for('routes.home'))
