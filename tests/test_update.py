import pytest
from marshmallow import ValidationError

from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema


def test_schema_update_with_data_fields(db_models, data_model_obj):
    assert data_model_obj.integer_field == 10
    assert data_model_obj.big_integer_field == 1000
    assert data_model_obj.email_field == 'test@test.com'

    class TestSchema(ModelSchema):
        system_code = fields.Str(required=True)

        class Meta:
            model = db_models.DataFieldsModel
            fields = '__all__'

    # update only `integer` and `email` fields
    update_data = {
        'integer_field': 20,
        'email_field': 'new-email@test.com'
    }

    schema = TestSchema()

    errors = schema.validate(update_data, partial=True)

    assert len(errors) == 0
    updated_obj = schema.update(data_model_obj, validated_data=update_data)
    assert updated_obj.integer_field == update_data['integer_field']
    assert updated_obj.email_field == update_data['email_field']
    assert updated_obj.big_integer_field == 1000  # this field was not in update_data


def test_schema_update_with_invalid_data(db_models, data_model_obj):
    assert data_model_obj.email_field == 'test@test.com'

    class TestSchema(ModelSchema):
        system_code = fields.Str(required=True)

        class Meta:
            model = db_models.DataFieldsModel
            fields = '__all__'

    # update only `integer` and `email` fields
    update_data = {
        'email_field': 'invalid-email'
    }

    schema = TestSchema()

    errors = schema.validate(update_data, partial=True)

    assert len(errors) == 1
    with pytest.raises(ValidationError) as excinfo:
        schema.update(data_model_obj, validated_data=update_data)

    assert 'Not a valid email address' in str(excinfo.value)
