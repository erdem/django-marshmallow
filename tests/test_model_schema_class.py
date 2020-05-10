import pytest
from django.core.exceptions import ImproperlyConfigured

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
        # given ... ModelSchema class implementation with including all model fields
        class TestModelSchema(ModelSchema):
            class Meta:
                model = db_models.DataFieldsModel
                fields = '__all__'

        schema = TestModelSchema()

        # then ... serialized data field names should match with django model fields
        model_fields = db_models.DataFieldsModel._meta.fields
        model_field_names = [f.name for f in model_fields]
        schema_field_names = list(schema.fields.keys())
        assert sorted(schema_field_names) == sorted(model_field_names)
