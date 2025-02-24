class Config:
    SECRET_KEY = 'your_secret_key'
    SESSION_TYPE = 'filesystem'

    MAIL_SERVER = 'smtp.yandex.ru'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'finmanager.notifications@yandex.ru'
    MAIL_PASSWORD = 'qbohfemvmiovcnno'
    MAIL_DEFAULT_SENDER = 'finmanager.notifications@yandex.ru'
