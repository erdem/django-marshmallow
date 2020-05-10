import os
import tempfile
from datetime import datetime
from decimal import Decimal

import pytest
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from django_marshmallow.schemas import ModelSchema


@pytest.fixture
def data_model_obj(db, db_models):
    instance = db_models.DataFieldsModel(
        big_integer_field=10000000,
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
    instance.file_field.save(os.path.join('media/test_tmp_file'), File(file_temp))
    file_temp.close()
    instance.save()
    return instance

