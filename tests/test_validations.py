import pytest

from django_marshmallow.schemas import ModelSchema


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
def o2o_related_instance(db_models):
    one_to_one_instance = db_models.OneToOneTarget(
        name='One to One'
    )
    one_to_one_instance.save()
    return one_to_one_instance


def test_invalid_primary_key_validation_for_foreign_key_fields(
    db,
    db_models,
    fk_related_instance,
    o2o_related_instance,
    m2m_related_instance
):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('foreign_key_field', )

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'foreign_key_field': {
            'id': 'INVALID STRING ID'
        }
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field']['id'] == ['Not a valid integer.']

    load_data = {
        'foreign_key_field': 'INVALID TYPE'
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == ['`RelatedField` data must be a mapping type.']

    load_data = {
        'foreign_key_field': {}
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == ['`RelatedField` data must be include a valid primary key value for ForeignKeyTarget model.']
