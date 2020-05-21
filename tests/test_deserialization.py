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


def test_related_fields_deserialization(
    db,
    db_models,
    fk_related_instance,
    o2o_related_instance,
    m2m_related_instance
):
    """
        Load a schema has related fields, the schema related fields should get primary keys as value.
    """
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')

    schema = TestSchema()

    load_data = {
        'name': 'Deserialized Instance',
        'foreign_key_field': {'id': fk_related_instance.id},
        'one_to_one_field': {'uuid': str(o2o_related_instance.uuid)},
        'many_to_many_field': [{'uuid': str(m2m_related_instance.uuid)}]
    }

    deserialized_data = schema.load(load_data)

    assert deserialized_data['name'] == 'Deserialized Instance'
    assert deserialized_data['foreign_key_field'].id == fk_related_instance.id
    assert deserialized_data['many_to_many_field'][0].uuid == m2m_related_instance.uuid
    assert deserialized_data['one_to_one_field'].uuid == o2o_related_instance.uuid


def test_related_pk_fields_deserialization(
    db,
    db_models,
    fk_related_instance,
    o2o_related_instance,
    m2m_related_instance,
):
    """
        Load a schema has related fields, the schema related fields should get primary keys as value.
    """
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')
            use_related_pk_fields = True

    schema = TestSchema()

    load_data = {
        'name': 'Deserialized Instance',
        'foreign_key_field': fk_related_instance.id,
        'one_to_one_field': str(o2o_related_instance.uuid),
        'many_to_many_field': [str(m2m_related_instance.uuid)]
    }

    deserialized_data = schema.load(load_data)

    assert deserialized_data['name'] == 'Deserialized Instance'
    assert deserialized_data['foreign_key_field'].id == fk_related_instance.id
    assert deserialized_data['many_to_many_field'][0].uuid == m2m_related_instance.uuid
    assert deserialized_data['one_to_one_field'].uuid == o2o_related_instance.uuid
