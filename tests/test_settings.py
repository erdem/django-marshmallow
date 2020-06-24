from django.test import override_settings

from django_marshmallow.schemas import ModelSchema
from django_marshmallow.settings import ma_settings


def test_expand_related_pk_fields_settings(
        db,
        db_models,
        fk_related_instance,
        settings
):
    MARSHMALLOW_SETTINGS = {
        'EXPAND_RELATED_PK_FIELDS': False
    }

    with override_settings(MARSHMALLOW_SETTINGS=MARSHMALLOW_SETTINGS):
        class TestSchema(ModelSchema):
            class Meta:
                model = db_models.AllRelatedFieldsModel
                fields = ('name', 'foreign_key_field')

        schema = TestSchema()

        load_data = {
            'name': 'Deserialized Instance',
            'foreign_key_field': fk_related_instance.id,
        }

        deserialized_data = schema.load(load_data)

        assert deserialized_data['name'] == 'Deserialized Instance'
        assert deserialized_data['foreign_key_field'].id == fk_related_instance.id
