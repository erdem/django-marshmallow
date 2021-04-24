import mimetypes
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from PIL import Image
from io import BytesIO
from types import SimpleNamespace

import django
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.conf import settings

import pytest
from django.db import transaction


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
        ),
        DEFAULT_AUTO_FIELD='django.db.models.AutoField'
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
def file_field_obj(db, db_models, uploaded_file_obj, uploaded_image_file_obj):
    obj = db_models.FileFieldModel(
        name='File field instance',
        file_field=uploaded_file_obj,
        image_field=uploaded_image_file_obj
    )
    obj.save()
    return obj


@pytest.fixture
def fk_related_instance(db_models):
    foreign_key_instnace = db_models.ForeignKeyTarget(
        name='Foreign Key'
    )
    foreign_key_instnace.save()
    return foreign_key_instnace


@pytest.fixture
def m2m_related_instance(db_models):
    many_to_many_instance = db_models.ManyToManyTarget(
        name='Many to Many'
    )
    many_to_many_instance.save()
    return many_to_many_instance


@pytest.fixture
def m2m_related_instances(db_models):
    many_to_many_instance_1 = db_models.ManyToManyTarget(
        name='Many to Many 1'
    )
    many_to_many_instance_1.save()

    many_to_many_instance_2 = db_models.ManyToManyTarget(
        name='Many to Many 2'
    )
    many_to_many_instance_2.save()
    m2m_instances = [
        many_to_many_instance_1,
        many_to_many_instance_2
    ]
    return m2m_instances


@pytest.fixture
def o2o_related_instance(db_models):
    one_to_one_instance = db_models.OneToOneTarget(
        name='One to One'
    )
    one_to_one_instance.save()
    return one_to_one_instance


@pytest.fixture
def data_model_obj(db, db_models):
    instance = db_models.DataFieldsModel(
        big_integer_field=1000,
        boolean_field=False,
        char_field='This a char field',
        date_field=datetime.today(),
        datetime_field=datetime.now(),
        decimal_field=Decimal('3.56'),
        email_field='test@test.com',
        float_field=1.45,
        integer_field=10,
        null_boolean_field=None,
        positive_integer_field=200000,
        positive_small_integer_field=10,
        small_integer_field=20,
        text_field="The text field value",
        time_field=datetime.now().time(),
        url_field="http://www.test.com",
        custom_field="custom field text",
        file_path_field=os.listdir(tempfile.gettempdir())[0]
    )

    file_temp = NamedTemporaryFile(delete=True)
    file_temp.write(file_temp.read(1))
    file_temp.flush()
    instance.file_field.save('test_file', File(file_temp))
    file_temp.close()
    instance.save()
    return instance


@pytest.fixture
def all_related_obj(db, db_models):
    one_to_one_instance = db_models.OneToOneTarget(
        name='One to One'
    )
    one_to_one_instance.save()
    foreign_key_instnace = db_models.ForeignKeyTarget(
        name='Foreign Key'
    )
    foreign_key_instnace.save()
    many_to_many_instance_1 = db_models.ManyToManyTarget(
        name='Many to Many 1'
    )
    many_to_many_instance_1.save()

    m2m_foreign_key_instnace = db_models.ForeignKeyTarget(
        name='Second level relation'
    )
    m2m_foreign_key_instnace.save()
    many_to_many_instance_2 = db_models.ManyToManyTarget(
        name='Many to Many 2',
    )
    many_to_many_instance_2.second_depth_relation_field = m2m_foreign_key_instnace
    many_to_many_instance_2.save()

    many_to_many_instances = [
        many_to_many_instance_1,
        many_to_many_instance_2
    ]
    all_related_obj = db_models.AllRelatedFieldsModel(
        name='All related model',
        one_to_one_field=one_to_one_instance,
        foreign_key_field = foreign_key_instnace
    )

    with transaction.atomic():
        all_related_obj.save()
        all_related_obj.many_to_many_field.set(many_to_many_instances)

    all_related_obj = db_models.AllRelatedFieldsModel.objects.get(pk=all_related_obj.pk)
    return all_related_obj


@pytest.fixture
def limited_related_choices_obj(db, db_models):
    objs = db_models.ForeignKeyTarget.objects.bulk_create([
        db_models.ForeignKeyTarget(name='Foreign Key 1', active=True),
        db_models.ForeignKeyTarget(name='Foreign Key 2', active=True),
        db_models.ForeignKeyTarget(name='Foreign Key 3', active=False),
        db_models.ForeignKeyTarget(name='Foreign Key 4', active=False),
        db_models.ForeignKeyTarget(name='Foreign Key 5', active=False)
    ])
    objs[0].save()
    simple_obj = db_models.SimpleRelationsModel(
        foreign_key_field=objs[0]
    )
    simple_obj.save()
    return simple_obj

