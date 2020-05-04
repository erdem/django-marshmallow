from types import SimpleNamespace

import django
from _pytest.outcomes import Failed
from django.conf import settings

import pytest


def pytest_report_header(config):
    return f'Tests running on Django {django.get_version()}'


def pytest_configure(config):
    settings.configure(
        DEBUG=False,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        INSTALLED_APPS=(
            'django_marshmallow',
            'tests'
        )
    )
    django.setup()


@pytest.fixture(scope='session', autouse=True)
def db_models():
    from tests import models as test_models

    # check all test models are valid to migrate
    model_classes = test_models.TestAbstractModel.__subclasses__()
    migrations_validation_erros = [m.check() for m in model_classes]
    if any(migrations_validation_erros):
        error_msgs = [str(erros) for erros in migrations_validation_erros if erros]
        pytest.exit(
            f'Some DB test models are not valid to migrate, check `tests/models.py`.'
            f'Errors: {error_msgs}')

    return SimpleNamespace(
        SimpleRegularModel=test_models.SimpleRegularModel,
        RegularFieldsModel=test_models.RegularFieldsModel,
        FieldOptionsModel=test_models.FieldOptionsModel,
        ChoicesModel=test_models.ChoicesModel,
        UniqueChoiceModel=test_models.UniqueChoiceModel,
    )
