import os
from types import SimpleNamespace

import django
import pytest
from django.db import connection
from django.test.utils import setup_test_environment

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'


def pytest_configure(config):
    django.setup()
