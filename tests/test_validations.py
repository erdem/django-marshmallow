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


@pytest.mark.parametrize(
    'schema_fields_option',
    [
        '__all__',
        ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')
    ]
)
def test_deserialization_related_primary_key_fields(
    db,
    db_models,
    fk_related_instance,
    o2o_related_instance,
    m2m_related_instance,
    schema_fields_option
):
    """
        Load a schema has related fields, the schema related fields should get primary keys as value.
    """
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = schema_fields_option

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'name': 'Deserialized Instance',
        'one_to_one_field': {'uuid': o2o_related_instance.uuid},
        'foreign_key_field': "test",
        'many_to_many_field': [{'uuid': m2m_related_instance.uuid}]
    }

    validated_data = schema.validate(load_data)

    entity = db_models.AllRelatedFieldsModel.objects.first()
