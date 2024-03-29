from urllib.parse import urljoin

from django.forms import model_to_dict

from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema
from tests.models import DECIMAL_CHOICES


def test_schema_serialization_with_all_fields_option(db_models, data_model_obj):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.DataFieldsModel
            fields = '__all__'

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


def test_choices_field_serialization(db, db_models):
    basic_choice_obj = db_models.BasicChoiceFieldModel(
        color='red'
    )
    basic_choice_obj.save()

    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.BasicChoiceFieldModel
            fields = ('color', )

    schema = TestSchema()
    data = schema.dump(basic_choice_obj)
    assert len(data) == 1
    assert data['color'] == 'red'

    # test same schema with `show_select_options`
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.BasicChoiceFieldModel
            fields = ('color', )
            show_select_options = True

    schema = TestSchema()
    data = schema.dump(basic_choice_obj)
    assert len(data) == 1
    assert data['color']['value'] == 'red'
    assert data['color']['options'] == list(db_models.BasicChoiceFieldModel.COLOR_CHOICES)


def test_file_field_serialization(db_models, file_field_obj):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.FileFieldModel
            fields = ('name', 'file_field', 'image_field')

    schema = TestSchema()
    data = schema.dump(file_field_obj)
    assert len(data) == 3
    assert data['name'] == file_field_obj.name
    assert data['file_field'] == file_field_obj.file_field.url
    assert data['image_field'] == file_field_obj.image_field.url

    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.FileFieldModel
            fields = ('name', 'file_field', 'image_field')
            use_file_url = False

    schema = TestSchema()
    data = schema.dump(file_field_obj)
    assert len(data) == 3
    assert data['name'] == file_field_obj.name

    # file fields serialize file names instead of file URLs
    assert data['file_field'] == file_field_obj.file_field.name
    assert data['image_field'] == file_field_obj.image_field.name

    custom_files_domain = 'http://test-server'
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.FileFieldModel
            fields = ('name', 'file_field', 'image_field')
            domain_for_file_urls = custom_files_domain
            use_file_url = True

    schema = TestSchema()
    data = schema.dump(file_field_obj)
    assert len(data) == 3
    assert data['name'] == file_field_obj.name

    assert data['file_field'] == urljoin(
        custom_files_domain,
        file_field_obj.file_field.url
    )
    assert data['image_field'] == urljoin(
        custom_files_domain,
        file_field_obj.image_field.url
    )


def test_schema_serialization_with_related_fields(db_models, all_related_obj):
    """
        Related fields primary keys should return right data types
    """
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = '__all__'

    schema = TestSchema()
    data = schema.dump(all_related_obj)

    assert data['name'] == all_related_obj.name
    assert isinstance(data['foreign_key_field'], dict) is True
    assert isinstance(data['one_to_one_field'], dict) is True
    assert isinstance(data['many_to_many_field'], list) is True

    assert data['foreign_key_field']['id'] == all_related_obj.foreign_key_field.id
    assert data['one_to_one_field']['uuid'] == str(all_related_obj.one_to_one_field.uuid)
    assert data['many_to_many_field'][0]['uuid'] == str(all_related_obj.many_to_many_field.all().first().uuid)


def test_schema_serialization_with_nested_schema(db_models, all_related_obj):
    class M2MSchema(ModelSchema):

        class Meta:
            model = db_models.ManyToManyTarget
            fields = ('uuid', 'name')
            order_by = ('-created_at',)

    class TestSchema(ModelSchema):
        many_to_many_field = fields.RelatedNested(M2MSchema, many=True)

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'many_to_many_field')

    schema = TestSchema()
    data = schema.dump(all_related_obj)

    assert isinstance(data['many_to_many_field'], list) is True
    m2m_queryset = all_related_obj.many_to_many_field.all().order_by('-created_at')
    assert data['many_to_many_field'][0]['uuid'] == str(m2m_queryset[0].uuid)
    assert data['many_to_many_field'][0]['name'] == str(m2m_queryset[0].name)
    assert data['many_to_many_field'][1]['uuid'] == str(m2m_queryset[1].uuid)
    assert data['many_to_many_field'][1]['name'] == str(m2m_queryset[1].name)


def test_implicit_nested_fields_schema(db, db_models, all_related_obj):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'many_to_many_field')
            nested_fields = {
                'many_to_many_field': {
                    'fields': ('uuid', 'name'),
                    'order_by': ('-created_at',)
                }
            }

    schema = TestSchema()
    data = schema.dump(all_related_obj)

    m2m_queryset = all_related_obj.many_to_many_field.all().order_by('-created_at')

    assert isinstance(data['many_to_many_field'], list) is True

    assert data['many_to_many_field'][0]['uuid'] == str(m2m_queryset[0].uuid)
    assert data['many_to_many_field'][0]['name'] == str(m2m_queryset[0].name)
    assert data['many_to_many_field'][1]['uuid'] == str(m2m_queryset[1].uuid)
    assert data['many_to_many_field'][1]['name'] == str(m2m_queryset[1].name)

    # Test multi-level `nested_fields` serialization

    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'many_to_many_field')
            nested_fields = {
                'many_to_many_field': {
                    'fields': ('uuid', 'name', 'second_depth_relation_field'),
                    'nested_fields': ('second_depth_relation_field', ),
                    'order_by': ('-created_at',)
                }
            }

    schema = TestSchema()
    data = schema.dump(all_related_obj)

    assert isinstance(data['many_to_many_field'], list) is True

    assert data['many_to_many_field'][0]['uuid'] == str(m2m_queryset[0].uuid)
    assert data['many_to_many_field'][0]['name'] == str(m2m_queryset[0].name)
    assert data['many_to_many_field'][1]['uuid'] == str(m2m_queryset[1].uuid)
    assert data['many_to_many_field'][1]['name'] == str(m2m_queryset[1].name)

    # `second_depth_relation_field` is a NestedSchema
    assert isinstance(data['many_to_many_field'][0]['second_depth_relation_field'], dict) is True
    assert data['many_to_many_field'][0]['second_depth_relation_field']['name'] == 'Second level relation'


def test_related_field_with_limited_choices_serialization(db_models, limited_related_choices_obj):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.SimpleRelationsModel
            fields = ('many_to_many_field', 'foreign_key_field')

    schema = TestSchema()
    data = schema.dump(limited_related_choices_obj)
    assert len(data) == 2


def test_custom_model_field_serialization(db, db_models):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.CustomFieldModel
            fields = ('choices',)

    model_obj = db_models.CustomFieldModel(
        choices=DECIMAL_CHOICES[1][0]
    )
    model_obj.save()
    schema = TestSchema()
    data = schema.dump(model_obj)
    assert len(data) == 1
    assert data['choices'] == DECIMAL_CHOICES[1][0]


def test_unknown_model_field_serialization(db, db_models):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.JSONFieldModel
            fields = ('name', 'data')

    json_data = {
        'schema_field_type': 'unknown'
    }
    model_obj = db_models.JSONFieldModel(
        name='store-json',
        data=json_data
    )
    model_obj.save()
    schema = TestSchema()
    dump_data = schema.dump(model_obj)
    assert dump_data['data'] == json_data
