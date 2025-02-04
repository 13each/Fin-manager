import os
from flask import Flask
from flask_session import Session
from app.models import init_db

def create_app():
    app = Flask(__name__)

    # Настройки приложения
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')

    # Инициализация сессий
    Session(app)

    # Инициализация базы данных
    with app.app_context():
        init_db()

    # Регистрация маршрутов
    from app.routes import routes
    app.register_blueprint(routes)

    return app
