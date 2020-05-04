import pytest

from django_marshmallow.schemas import ModelSchema


@pytest.fixture
def simple_item(db, db_models):
    model_instace = db_models.SimpleRegularModel(
        char_field='simple char'
    )
    model_instace.save()
    return model_instace


@pytest.mark.django_db
def test_regular_model(db, db_models, simple_item):

    class SimpleModelSchema(ModelSchema):

        class Meta:
            fields = '__all__'
            model = db_models.SimpleRegularModel

    model_schema = SimpleModelSchema()
    assert 'char_field' in model_schema.dump(simple_item)
