import pytest
from django.core.exceptions import ImproperlyConfigured

from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema


class TestModelSchemaOptions:

    def test_schema_model_option_validation(self):
        # given ... ModelSchema class implementation without `Meta.model` attribute
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    pass

        # then ... should raise `ImproperlyConfigured` exception
        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == 'Creating a ModelSchema without `Meta.model` attribute is prohibited; ' \
                            'TestModelSchema schema class needs updating.'

    def test_schema_fields_and_exclude_options_validation(self, db_models):
        # given ... ModelSchema class implementation without `Meta.fields` and `Meta.exclude` attributes
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel

        # then ... should raise `ImproperlyConfigured` exception
        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == 'Creating a ModelSchema without either `Meta.fields` attribute or `Meta.exclude`' \
                            ' attribute is prohibited; TestModelSchema schema class needs updating.'

        # given ... ModelSchema class implementation with invalid `Meta.fields` data type
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    fields = {}

        # then ... should raise `ValueError` exception
        error_msg = exc_info.value.args[0]
        assert exc_info.type == ValueError
        assert error_msg == '`fields` option must be a list or tuple.'

        # given ... ModelSchema class implementation with invalid `Meta.exclude` data type
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    exclude = {}

        # then ... should raise `ValueError` exception
        error_msg = exc_info.value.args[0]
        assert exc_info.type == ValueError
        assert error_msg == '`exclude` must be a list or tuple.'

        # given ... ModelSchema class implementation has Meta.fields and Meta.exclude attributes
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('id', )
                    exclude = ('name', )

        # then ... should raise `ValueError` exception
        error_msg = exc_info.value.args[0]
        assert exc_info.type == ImproperlyConfigured
        assert error_msg == 'Cannot set `fields` and `exclude` options both together on model schemas.' \
                            'ModelSchemaMetaclass schema class needs updating.'

    def test_schema_level_option_validation(self, db_models):
        # given ... ModelSchema class implementation has negative `level` value
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('id', )
                    level = -1

        # then ... should raise `AssertionError` exception
        error_msg = exc_info.value.args[0]
        assert exc_info.type == AssertionError
        assert error_msg == '`level` cannot be negative. ModelSchemaMetaclass schema class schema class needs updating.'

        # given ... ModelSchema class implementation has greater than 10 `level` value
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel
                    fields = ('id', )
                    level = 11

        # then ... should raise `AssertionError` exception
        error_msg = exc_info.value.args[0]
        assert exc_info.type == AssertionError
        assert error_msg == '`level` cannot be greater than 10. ModelSchemaMetaclass schema class schema class needs updating.'

    def test_schema_ordered_option_functionality(self, db_models):
        # given ... expected fields for testing django model
        expected_fields = ('id', 'name', 'text', 'published_date', 'created_at')

        # ... ModelSchema class implementation with Meta.ordered (Meta.ordered `True` by default)
        class TestModelSchema(ModelSchema):

            class Meta:
                model = db_models.SimpleTestModel
                fields = expected_fields

        # ... ModelSchema class instance
        schema = TestModelSchema()

        # then ... Schema field names should match with `expected_fields`
        assert tuple(schema.fields.keys()) == expected_fields

        # given ... ModelSchema class with Meta.ordered=False
        class TestModelSchema(ModelSchema):

            class Meta:
                model = db_models.SimpleTestModel
                fields = expected_fields
                ordered = False

        # ... ModelSchema class instance
        schema = TestModelSchema()

        # then ... Schema field names should not match with `expected_fields`
        assert len(tuple(schema.fields.keys())) == len(expected_fields)
        assert not tuple(schema.fields.keys()) == expected_fields


class TestModelSchemaFieldConverter:

    def test_generated_schema_fields_for_all_fields_option(self, db_models):
        # given ... ModelSchema class implementation including all data model fields
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.DataFieldsModel
                fields = '__all__'

        schema = TestModelSchema()

        # then ... serialized data fields should match with django model fields
        model_fields = db_models.DataFieldsModel._meta.fields
        model_field_names = [f.name for f in model_fields]
        schema_field_names = list(schema.fields.keys())
        assert sorted(schema_field_names) == sorted(model_field_names)

    def test_generated_related_schema_fields(self, db_models):
        # given ... ModelSchema class implementation (Model has related fields)
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.SimpleRelationsModel
                fields = ('foreign_key_field', 'many_to_many_field')

        schema = TestModelSchema()

        # then ... Schema `related_fields` method should return `2` fields
        assert len(schema.related_fields.keys()) == 2
        # ... Schema ManyToManyField representation field should have `many=True`
        assert schema.related_fields['many_to_many_field'].many is True
        # ... Schema ManyToManyField representation field should have `many=False`
        assert schema.related_fields['foreign_key_field'].many is False
        # ... Model Related fields should represented as `RelatedField` on schema class
        assert isinstance(schema.related_fields['many_to_many_field'], fields.RelatedField)
        assert isinstance(schema.related_fields['foreign_key_field'], fields.RelatedField)

    @pytest.mark.parametrize("schema_fields_option", ['__all__', ('foreign_key_field', 'many_to_many_field')])
    def test_generated_related_nested_fields(self, db_models, schema_fields_option):
        # given ... ModelSchema class implementation has nested level
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.SimpleRelationsModel
                fields = schema_fields_option
                level = 1

        schema = TestModelSchema()
        # then ... Schema `related_fields` method should return `2` fields
        assert len(schema.related_fields.keys()) == 2
        # ... Schema ManyToManyField representation field should have `many=True`
        assert schema.related_fields['many_to_many_field'].many is True
        # ... Schema ManyToManyField representation field should have `many=False`
        assert schema.related_fields['foreign_key_field'].many is False
        # ... Model Related Nested fields should represented as `RelatedNested` on schema class
        assert isinstance(schema.related_fields['many_to_many_field'], fields.RelatedNested)
        assert isinstance(schema.related_fields['foreign_key_field'], fields.RelatedNested)
        # ... RelatedNested schema fields should match with django model fields
        nested_schema = schema.related_fields['many_to_many_field'].schema
        nested_model_fields = db_models.ManyToManyTarget._meta.fields
        nested_model_field_names = [f.name for f in nested_model_fields]
        nested_schema_field_names = list(nested_schema.fields.keys())
        assert sorted(nested_schema_field_names) == sorted(nested_model_field_names)

    @pytest.mark.parametrize("schema_fields_option", ['__all__', ('foreign_key_field', 'many_to_many_field')])
    def test_second_level_generated_nested_schemas(self, db_models, schema_fields_option):
        # given ... ModelSchema class implementation (DB model has second level nested relation)
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.SimpleRelationsModel
                fields = schema_fields_option
                level = 2

        schema = TestModelSchema()

        # then ... ModelSchema should include second level related model fields
        first_level_nested_schema = schema.related_fields['many_to_many_field'].schema
        second_level_nested_schema = first_level_nested_schema.fields['second_level_relation_field'].schema
        second_level_relation_model = db_models.ForeignKeyTarget
        second_level_relation_model_field_names = [f.name for f in second_level_relation_model._meta.fields]
        second_level_nested_schema_field_names = list(second_level_nested_schema.fields.keys())
        assert sorted(second_level_relation_model_field_names) == sorted(second_level_nested_schema_field_names)
