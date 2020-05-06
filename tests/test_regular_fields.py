from datetime import datetime

import pytest

from django_marshmallow.schemas import ModelSchema


@pytest.fixture
def simple_item(db, db_models):
    model_instace = db_models.SimpleTestModel(
        name='Simple name',
        text='Text name',
        published_date=datetime.now()
    )
    model_instace.save()
    return model_instace


@pytest.mark.django_db
def test_regular_model_fields(db, db_models, simple_item):
    class SimpleModelSchema(ModelSchema):

        class Meta:
            fields = '__all__'
            model = db_models.SimpleTestModel

    model_schema = SimpleModelSchema()
    assert 'name' in model_schema.dump(simple_item)
