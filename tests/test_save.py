from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema
from tests.models import DECIMAL_CHOICES


def test_file_field_model_save(db, db_models, uploaded_file_obj, uploaded_image_file_obj):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.FileFieldModel
            fields = ('name', 'file_field', 'image_field')

    assert db_models.FileFieldModel.objects.count() == 0

    schema = TestSchema()
    save_data = {
        'name': 'Created instance',
        'file_field': uploaded_file_obj,
        'image_field': uploaded_image_file_obj
    }
    errors = schema.validate(save_data)
    instance = schema.save()
    assert len(errors) == 0
    assert db_models.FileFieldModel.objects.count() == 1
    assert db_models.FileFieldModel.objects.first().file_field.url == instance.file_field.url
    assert db_models.FileFieldModel.objects.first().image_field.url == instance.image_field.url


def test_related_nested_fields_save(db, db_models):
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

    save_data = {
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

    load_data = schema.load(save_data)
    assert len(load_data) == len(save_data)

    # no need to pass `validated_data` parameter to `save()` if load or validate method called.
    instance = schema.save()
    assert instance.pk is not None
    assert instance.foreign_key_field.name == save_data['foreign_key_field']['name']
    assert instance.one_to_one_field.name == save_data['one_to_one_field']['name']
    assert instance.many_to_many_field.all().count() == 2


def test_schema_with_related_pk_fields(db, db_models, fk_related_instance, m2m_related_instances):
    """
        Load a schema has related nested fields. Do not call save method of the schema.
    """
    db_models.AllRelatedFieldsModel.objects.all().delete()

    class O2ONestedSchema(ModelSchema):
        class Meta:
            model = db_models.OneToOneTarget
            fields = ('uuid', 'name')

    class TestSchema(ModelSchema):
        one_to_one_field = fields.RelatedNested(O2ONestedSchema)

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field', 'many_to_many_field', 'one_to_one_field')

    schema = TestSchema()

    save_data = {
        'name': 'Related Nested Instance',
        'foreign_key_field': {
            'pk': fk_related_instance.pk
        },
        'one_to_one_field': {
            'name': 'O2O instance name'
        },
        'many_to_many_field': [
            {
                'uuid': m2m_related_instances[0].pk
            },
            {
                'uuid': m2m_related_instances[1].pk
            }
        ]
    }

    errors = schema.validate(save_data)
    assert len(errors) == 0
    instance = schema.save(save_data)
    assert instance.pk is not None
    assert instance.foreign_key_field.id == fk_related_instance.id
    assert instance.one_to_one_field.name == save_data['one_to_one_field']['name']
    m2m_pk_list = list(instance.many_to_many_field.all().values_list('uuid', flat=True))
    assert m2m_related_instances[0].uuid in m2m_pk_list
    assert m2m_related_instances[1].uuid in m2m_pk_list


def test_custom_model_field_deserialization(db, db_models):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.CustomFieldModel
            fields = ('choices',)

    save_data = {
        'choices': DECIMAL_CHOICES[1][0]
    }
    schema = TestSchema()
    errors = schema.validate(save_data)
    assert len(errors) == 0
    instance = schema.save(save_data)
    assert instance.choices == DECIMAL_CHOICES[1][0]
