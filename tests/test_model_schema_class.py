import pytest
from django.core.exceptions import ImproperlyConfigured

from django_marshmallow.schemas import ModelSchema


class TestModelSchemaOptions:

    def test_schema_model_option_validation(self):
        # given ... A ModelSchema without `Meta.model` attribute
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    pass

        # then ... should raise `ImproperlyConfigured` exception
        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == 'Creating a ModelSchema without `Meta.model` attribute is prohibited; ' \
                            'TestModelSchema needs updating.'

    def test_schema_fields_and_exclude_options_validation(self, db_models):
        # given ... A ModelSchema without `Meta.fields` and `Meta.exclude` attributes
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    model = db_models.SimpleTestModel

        # then ... should raise `ImproperlyConfigured` exception
        assert exc_info.type == ImproperlyConfigured
        error_msg = exc_info.value.args[0]
        assert error_msg == 'Creating a ModelSchema without either `Meta.fields` attribute or `Meta.exclude`' \
                            ' attribute is prohibited; TestModelSchema needs updating.'

        # given ... A ModelSchema class with invalid `Meta.fields` data type
        with pytest.raises(Exception) as exc_info:
            class TestModelSchema(ModelSchema):
                class Meta:
                    fields = {}

        # then ... should raise `ValueError` exception
        error_msg = exc_info.value.args[0]
        assert exc_info.type == ValueError
        assert error_msg == '`fields` option must be a list or tuple.'

    def test_schema_fields_generated_for_model_fields(self, db_models):
        # given ... expected fields for testing django model
        expected_fields = ('id', 'name', 'text', 'published_date', 'created_at')

        # ... ModelSchema class implementation
        class TestModelSchema(ModelSchema):

            class Meta:
                model = db_models.SimpleTestModel
                fields = expected_fields

        # ... ModelSchema instance
        schema = TestModelSchema()

        # then ... Schema field names should match with `expected_fields`
        assert tuple(schema.fields.keys()) == expected_fields

