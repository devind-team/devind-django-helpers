"""Настройки Django для тестов."""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'sqlite3.db',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = (
    'tests',
)

MIDDLEWARE = []

USE_TZ = True

TIME_ZONE = 'UTC'

DOCUMENTS_DIR = ''
