import pytest
from django.core.exceptions import ImproperlyConfigured

from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema


class TestModelSchemaOptions:

    def test_schema_model_option_validation(self):
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    pass

        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == 'Creating a ModelSchema without `Meta.model` attribute is prohibited; ' \
                            'TestModelSchema schema class needs updating.'

        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = object()

        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == '`model` option must be a Django model class'

    def test_schema_fields_and_exclude_options_validation(self, db_models):
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel

        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == 'Creating a ModelSchema without `Meta.fields` attribute or `Meta.exclude` ' \
                            'or `Meta.include_pk` attribute is prohibited; TestModelSchema schema class needs updating.'

        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    fields = {}

        error_msg = exc_info.value.args[0]
        assert exc_info.type == ValueError
        assert error_msg == '`fields` option must be a list or tuple.'

        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    exclude = {}

        error_msg = exc_info.value.args[0]
        assert exc_info.type == ValueError
        assert error_msg == '`exclude` must be a list or tuple.'

        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('id', )
                    exclude = ('name', )

        error_msg = exc_info.value.args[0]
        assert exc_info.type == ImproperlyConfigured
        assert error_msg == 'Cannot set `fields` and `exclude` options both together on model schemas.' \
                            'ModelSchemaMetaclass schema class needs updating.'

    def test_schema_depth_option_validation(self, db_models):
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('id', )
                    depth = -1

        error_msg = exc_info.value.args[0]
        assert exc_info.type == AssertionError
        assert error_msg == '`depth` cannot be negative. ModelSchemaMetaclass schema class schema class needs updating.'

        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('id', )
                    depth = 11

        error_msg = exc_info.value.args[0]
        assert exc_info.type == AssertionError
        assert error_msg == '`depth` cannot be greater than 10. ModelSchemaMetaclass schema class schema class needs updating.'

    def test_schema_include_pk_option_validation(self, db_models):
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('name', )
                    include_pk = None

        error_msg = exc_info.value.args[0]
        assert exc_info.type == ValueError
        assert error_msg == '`include_pk` option must be a boolean.'

    def test_schema_ordered_option_functionality(self, db_models):
        expected_fields = ('id', 'name', 'text', 'published_date', 'created_at')

        class TestModelSchema(ModelSchema):

            class Meta:
                model = db_models.SimpleTestModel
                fields = expected_fields

        schema = TestModelSchema()

        assert tuple(schema.fields.keys()) == expected_fields

        class TestModelSchema(ModelSchema):

            class Meta:
                model = db_models.SimpleTestModel
                fields = expected_fields
                ordered = False

        schema = TestModelSchema()

        assert len(tuple(schema.fields.keys())) == len(expected_fields)
        assert not tuple(schema.fields.keys()) == expected_fields


class TestModelSchemaFieldConverter:

    def test_generated_schema_fields_for_all_fields_option(self, db_models):
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.DataFieldsModel
                fields = '__all__'

        schema = TestModelSchema()

        model_fields = db_models.DataFieldsModel._meta.fields
        model_field_names = [f.name for f in model_fields]
        schema_field_names = list(schema.fields.keys())
        assert sorted(schema_field_names) == sorted(model_field_names)

    def test_generated_related_schema_fields(self, db_models):
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.SimpleRelationsModel
                fields = ('foreign_key_field', 'many_to_many_field')

        schema = TestModelSchema()

        assert len(schema.related_fields.keys()) == 2
        assert schema.related_fields['many_to_many_field'].many is True
        assert schema.related_fields['foreign_key_field'].many is False
        assert isinstance(schema.related_fields['many_to_many_field'], fields.RelatedField)
        assert isinstance(schema.related_fields['foreign_key_field'], fields.RelatedField)

    def test_related_fields_data_types(self, db_models):
        """
            Related fields primary keys should be generated right schema fields
        """

        class TestModelSchema(ModelSchema):
            """
                Implements a schema has different type of related fields
            """

            class Meta:
                model = db_models.AllRelatedFieldsModel
                fields = ('foreign_key_field', 'many_to_many_field')

        schema = TestModelSchema()
        schema_foreign_key_field = schema.fields['foreign_key_field']
        foreign_key_related_schema = schema_foreign_key_field.schema
        fk_related_pk_field = foreign_key_related_schema.pk_field

        # ForeignKeyTarget model related schema should have integer primary key field
        assert isinstance(fk_related_pk_field, fields.Integer) is True

        schema_many_to_many_field = schema.fields['many_to_many_field']
        many_to_many_related_schema = schema_many_to_many_field.schema
        m2m_related_pk_field = many_to_many_related_schema.pk_field

        # ManyToManyTarget model related schema should have UUID primary key field
        assert isinstance(m2m_related_pk_field, fields.UUID) is True

    @pytest.mark.parametrize("schema_fields_option", ['__all__', ('foreign_key_field', 'many_to_many_field')])
    def test_generated_related_nested_fields(self, db_models, schema_fields_option):
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.SimpleRelationsModel
                fields = schema_fields_option
                depth = 1

        schema = TestModelSchema()
        assert len(schema.related_fields.keys()) == 2
        assert schema.related_fields['many_to_many_field'].many is True
        assert schema.related_fields['foreign_key_field'].many is False
        assert isinstance(schema.related_fields['many_to_many_field'], fields.RelatedNested)
        assert isinstance(schema.related_fields['foreign_key_field'], fields.RelatedNested)
        nested_schema = schema.related_fields['many_to_many_field'].schema
        nested_model_fields = db_models.ManyToManyTarget._meta.fields
        nested_model_field_names = [f.name for f in nested_model_fields]
        nested_schema_field_names = list(nested_schema.fields.keys())
        assert sorted(nested_schema_field_names) == sorted(nested_model_field_names)

    @pytest.mark.parametrize("schema_fields_option", ['__all__', ('foreign_key_field', 'many_to_many_field')])
    def test_second_depth_generated_nested_schemas(self, db_models, schema_fields_option):
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.SimpleRelationsModel
                fields = schema_fields_option
                depth = 2

        schema = TestModelSchema()

        first_depth_nested_schema = schema.related_fields['many_to_many_field'].schema
        second_depth_nested_schema = first_depth_nested_schema.fields['second_depth_relation_field'].schema
        second_depth_relation_model = db_models.ForeignKeyTarget
        second_depth_relation_model_field_names = [f.name for f in second_depth_relation_model._meta.fields]
        second_depth_nested_schema_field_names = list(second_depth_nested_schema.fields.keys())
        assert sorted(second_depth_relation_model_field_names) == sorted(second_depth_nested_schema_field_names)
