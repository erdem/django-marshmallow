import os
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_PATH = os.path.normpath(os.path.join(SITE_PATH, '..', '..'))
if PROJECT_PATH not in sys.path or SITE_PATH not in sys.path:
    sys.path.insert(2, PROJECT_PATH)
    sys.path.insert(1, BASE_DIR)
    sys.path.insert(0, SITE_PATH)


SECRET_KEY = '8&q!1*r95%9lje^1r8tc5-*#(!0*_(5r$p@su91p&7_x*&kmin'
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_marshmallow',
    'tests'
]

_fd, _filename = tempfile.mkstemp(prefix="test_")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'TEST': {'NAME': _filename},
    }
}
