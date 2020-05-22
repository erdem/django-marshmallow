import pytest

from django_marshmallow import fields
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


def test_related_nested_fields_deserialization(
        db,
        db_models
):
    """
        Load a schema has related nested fields. Do not call save method of the schema.
    """
    db_models.AllRelatedFieldsModel.objects.all().delete()

    class FKNestedSchema(ModelSchema):
        class Meta:
            model = db_models.ForeignKeyTarget
            fields = ('id', 'name',)

    class M2MNestedSchema(ModelSchema):
        class Meta:
            model = db_models.ManyToManyTarget
            fields = ('name',)

    class O2ONestedSchema(ModelSchema):
        class Meta:
            model = db_models.OneToOneTarget
            fields = ('uuid', 'name')

    class TestSchema(ModelSchema):
        foreign_key_field = fields.RelatedNested(FKNestedSchema)
        many_to_many_field = fields.RelatedNested(M2MNestedSchema, many=True)
        one_to_one_field = fields.RelatedNested(O2ONestedSchema)

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')

    schema = TestSchema()

    load_data = {
        'name': 'Related Nested Instance',
        'foreign_key_field': {
            'name': 'foreign instance name'
        },
        'one_to_one_field': {
            'name': 'O2O instance name'
        },
        'many_to_many_field': [
            {
                'name': 'M2M instance 1'
            },
            {
                'name': 'M2M instance 2'
            }
        ]
    }

    deserialized_data = schema.load(load_data)

    # check instance didn't call save mehtod when deserializing data
    assert db_models.ForeignKeyTarget.objects.all().count() == 0
    assert db_models.ManyToManyTarget.objects.all().count() == 0
    assert db_models.OneToOneTarget.objects.all().count() == 0
    assert db_models.AllRelatedFieldsModel.objects.all().count() == 0

    assert deserialized_data['name'] == load_data['name']
    fk_instance = deserialized_data['foreign_key_field']
    assert isinstance(fk_instance, db_models.ForeignKeyTarget) is True
    assert fk_instance.pk is None

    m2m_instnaces = deserialized_data['many_to_many_field']
    assert all([isinstance(m, db_models.ManyToManyTarget) for m in m2m_instnaces]) is True

    # Django instance won't `None` if there is a custom primary key field
    assert all([m.pk is not None for m in m2m_instnaces]) is True
    # check instance state to find out object is saved
    assert all([m._state.adding is True for m in m2m_instnaces]) is True

    o2o_instance = deserialized_data['one_to_one_field']
    assert isinstance(o2o_instance, db_models.OneToOneTarget) is True
    assert o2o_instance.uuid is not None
    assert o2o_instance._state.adding is True
