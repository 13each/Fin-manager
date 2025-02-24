import os
from flask import Flask
from flask_session import Session
from flask_mail import Mail
from app.models import init_db

mail = Mail()


def create_app():
    app = Flask(__name__)

    app.config.from_object('app.config.Config')

    mail.init_app(app)

    # Настройки сессий
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')

    Session(app)

    # Инициализация базы данных
    with app.app_context():
        init_db()

    # Регистрация маршрутов
    from app.routes import routes
    app.register_blueprint(routes)

    return app
