from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema
from tests.models import DECIMAL_CHOICES


def test_choices_field_deserialization(db, db_models):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.BasicChoiceFieldModel
            fields = ('color',)

    load_data = {
        'color': 'red'
    }

    schema = TestSchema()
    data = schema.load(load_data)
    assert len(data) == 1
    assert data['color'] == 'red'

    # test same schema with `show_select_options`

    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.BasicChoiceFieldModel
            fields = ('color',)
            show_select_options = True

    load_data = {
        'color': 'red'
    }

    schema = TestSchema()
    data = schema.load(load_data)
    assert len(data) == 1
    assert data['color'] == 'red'


def test_custom_model_field_deserialization(db, db_models):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.CustomFieldModel
            fields = ('choices',)

    load_data = {
        'choices': DECIMAL_CHOICES[1][0]
    }
    schema = TestSchema()
    data = schema.load(load_data)
    assert len(data) == 1
    assert data['choices'] == DECIMAL_CHOICES[1][0]


# related field tests

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
            expand_related_pk_fields = False

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

    # test without `foreign_key_field` field, it is a non-required field.

    load_data = {
        'name': 'Deserialized Instance',
        'one_to_one_field': str(o2o_related_instance.uuid),
        'many_to_many_field': [str(m2m_related_instance.uuid)]
    }

    deserialized_data = schema.load(load_data)

    assert deserialized_data['name'] == 'Deserialized Instance'
    assert deserialized_data['foreign_key_field'] is None
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
        foreign_key_field = fields.RelatedNested(FKNestedSchema, required=False, allow_none=True)
        many_to_many_field = fields.RelatedNested(M2MNestedSchema, many=True)
        one_to_one_field = fields.RelatedNested(O2ONestedSchema)

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')

    schema = TestSchema()

    load_data = {
        'name': 'Related Nested Instance',
        'foreign_key_field': None,
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
    assert fk_instance is None

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


def test_implicit_related_nested_fields_deserialization(db, db_models):
    """
        Load a schema has related nested fields. Do not call save method of the schema.
    """
    db_models.AllRelatedFieldsModel.objects.all().delete()

    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')
            nested_fields = {
                'foreign_key_field': {
                    'fields': ('id', 'name')
                },
                'many_to_many_field': {
                    'fields': ('name',)
                },
                'one_to_one_field': {
                    'fields': ('uuid', 'name')
                }
            }

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

def test_file_field_deserialization(db_models, uploaded_file_obj, uploaded_image_file_obj):

    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.FileFieldModel
            fields = ('name', 'file_field', 'image_field')

    name = 'test file and image fields'
    load_data = {
        'name': name,
        'file_field': uploaded_file_obj,
        'image_field': uploaded_image_file_obj
    }
    schema = TestSchema()
    data = schema.load(load_data)
    assert len(data) == 3
    assert data['name'] == name
    assert data['file_field'].name == uploaded_file_obj.name
    assert data['image_field'].name == uploaded_image_file_obj.name


def test_related_field_with_limited_choices_deserialization(db_models, limited_related_choices_obj):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.SimpleRelationsModel
            fields = ('foreign_key_field', )

    # `foreign_key_field` choices limited for only `active=True` items
    choice = db_models.ForeignKeyTarget.objects.filter(active=True).first()
    schema = TestSchema()
    load_data = {
        'foreign_key_field': {
            'pk': choice.id
        }
    }
    data = schema.load(load_data)
    assert len(data) == 1
    assert data['foreign_key_field'] == choice
