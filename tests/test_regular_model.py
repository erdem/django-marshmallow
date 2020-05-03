import pytest

from django_marshmallow.schemas import ModelSchema
from .models import SimpleRegularModel


@pytest.fixture
def simple_item(db):
    model_instace = SimpleRegularModel(
        char_field='simple char'
    )
    model_instace.save()
    return model_instace


class Test2:

    @pytest.mark.django_db
    def test_regular_model(self, db, simple_item):

        class SimpleModelSchema(ModelSchema):

            class Meta:
                fields = '__all__'
                model = SimpleRegularModel

        model_schema = SimpleModelSchema()
        assert 'char_field' in model_schema.dump(simple_item)
