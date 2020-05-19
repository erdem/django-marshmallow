import os
import tempfile
from datetime import datetime
from decimal import Decimal
from collections import OrderedDict

import pytest
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.forms import model_to_dict

from django_marshmallow import fields
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
    instance.file_field.save(os.path.join('tests/media/test_tmp_file'), File(file_temp))
    file_temp.close()
    instance.save()
    return instance


def test_schema_serialization_with_all_fields_option(db_models, data_model_obj):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.DataFieldsModel
            fields = '__all__'
            include_pk = True

    schema = TestSchema()
    data = schema.dump(data_model_obj)
    assert sorted(data.keys()) == sorted(model_to_dict(data_model_obj).keys())


def test_schema_serialization_with_auto_generated_fields(db_models, data_model_obj):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.DataFieldsModel
            fields = ('big_integer_field', 'email_field')

    schema = TestSchema()
    data = schema.dump(data_model_obj)
    assert len(data.keys()) == 2
    assert data['big_integer_field'] == data_model_obj.big_integer_field
    assert data['email_field'] == data_model_obj.email_field


def test_schema_serialization_with_declared_fields(db_models, data_model_obj):
    """
        Declared fields should override the auto-generated fields
    """
    class TestSchema(ModelSchema):
        big_integer_field = fields.String()
        test_field = fields.Integer()

        class Meta:
            model = db_models.DataFieldsModel
            fields = ('big_integer_field', 'test_field')

    schema = TestSchema()
    data_model_obj.test_field = 123
    data = schema.dump(data_model_obj)
    assert len(data.keys()) == 2
    assert data['big_integer_field'] == str(data_model_obj.big_integer_field)
    assert data['test_field'] == 123


@pytest.fixture
def related_model_obj(db, db_models):
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
    many_to_many_instance_2 = db_models.ManyToManyTarget(
        name='Many to Many 2'
    )
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
    all_related_obj.save()
    all_related_obj.many_to_many_field.set(many_to_many_instances)
    return all_related_obj


def test_schema_serialization_with_related_fields(db_models, related_model_obj):
    """
        Related fields primary keys should return right data types
    """
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = '__all__'

    schema = TestSchema()
    data = schema.dump(related_model_obj)

    assert data['name'] == related_model_obj.name
    assert isinstance(data['foreign_key_field'], OrderedDict) is True
    assert isinstance(data['one_to_one_field'], OrderedDict) is True
    assert isinstance(data['many_to_many_field'], list) is True

    assert data['foreign_key_field']['id'] == related_model_obj.foreign_key_field.id
    assert data['one_to_one_field']['uuid'] == str(related_model_obj.one_to_one_field.uuid)
    assert data['many_to_many_field'][0]['uuid'] == str(related_model_obj.many_to_many_field.all().first().uuid)


def test_schema_serialization_with_nested_declared_fields(db_models):
    pass

