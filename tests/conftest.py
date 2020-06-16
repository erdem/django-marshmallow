import mimetypes
from PIL import Image
from io import BytesIO
from types import SimpleNamespace

import django
from django.core.files.uploadedfile import InMemoryUploadedFile
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
        pytest.fail(
            f'Some DB test models are not valid to migrate, check `tests/models.py`.'
            f'Errors: {error_msgs}'
        )

    return SimpleNamespace(**dict(
        [(model_class.__name__, model_class) for model_class in model_classes]
    ))


@pytest.fixture
def uploaded_file_obj():
    fi = BytesIO(b'This is a test file.')

    def getsize(f):
        f.seek(0)
        f.read()
        s = f.tell()
        f.seek(0)
        return s

    name = 'test_file.txt'
    content_type, charset = mimetypes.guess_type(name)
    size = getsize(fi)
    return InMemoryUploadedFile(
        file=fi,
        field_name=None,
        name=name,
        content_type=content_type,
        charset=charset,
        size=size
    )


@pytest.fixture
def uploaded_image_file_obj():
    im = Image.new(mode='RGB', size=(400, 400))
    im_io = BytesIO()
    im.save(im_io, 'jpeg')
    im_io.seek(0)

    return InMemoryUploadedFile(
        file=im_io,
        field_name=None,
        name='test_image.jpg',
        content_type='image/jpeg',
        size=len(im_io.getvalue()),
        charset=None
    )


@pytest.fixture
def file_field_obj(db_models, uploaded_file_obj, uploaded_image_file_obj):
    obj = db_models.FileFieldModel(
        name='File field instance',
        file_field=uploaded_file_obj,
        image_field=uploaded_image_file_obj
    )
    obj.save()
    return obj
