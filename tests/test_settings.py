from django.test import override_settings

from django_marshmallow.schemas import ModelSchema
from django_marshmallow.settings import DEFAULTS as MARSHMALLOW_DEFAULT_SETTINGS, ma_settings, DjangoMarshmallowSettings


def test_default_settings_values():
    with override_settings(MAP_WIDGETS={}):
        for setting_name, value in MARSHMALLOW_DEFAULT_SETTINGS.items():
            assert getattr(ma_settings, setting_name) == value


def test_custom_settings_values(settings):
    DATE_FORMAT = '%d/%m/%y'
    ORDERED = False
    INDEX_ERRORS = False
    ERROR_MESSAGE_OVERRIDES = {
        'one_field': 'field is invalid'
    }

    MARSHMALLOW_SETTINGS = {
        'DATE_FORMAT': DATE_FORMAT,
        'ORDERED': ORDERED,
        'INDEX_ERRORS': INDEX_ERRORS,
        'ERROR_MESSAGE_OVERRIDES': ERROR_MESSAGE_OVERRIDES
    }

    with override_settings(MARSHMALLOW_SETTINGS=MARSHMALLOW_SETTINGS):
        ma_settings = DjangoMarshmallowSettings()
        assert getattr(ma_settings, 'DATE_FORMAT') == DATE_FORMAT
        assert getattr(ma_settings, 'ORDERED') == ORDERED
        assert getattr(ma_settings, 'INDEX_ERRORS') == INDEX_ERRORS
        assert getattr(ma_settings, 'ERROR_MESSAGE_OVERRIDES') == ERROR_MESSAGE_OVERRIDES


def test_expand_related_pk_fields_settings(
        db,
        db_models,
        fk_related_instance,
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


def test_show_select_options_settings(db, db_models):
    basic_choice_obj = db_models.BasicChoiceFieldModel(
        color='blue'
    )
    basic_choice_obj.save()

    MARSHMALLOW_SETTINGS = {
        'SHOW_SELECT_OPTIONS': True
    }

    with override_settings(MARSHMALLOW_SETTINGS=MARSHMALLOW_SETTINGS):
        class TestSchema(ModelSchema):
            class Meta:
                model = db_models.BasicChoiceFieldModel
                fields = ('color',)

        schema = TestSchema()
        data = schema.dump(basic_choice_obj)
        assert len(data) == 1
        assert data['color']['value'] == 'blue'
        assert data['color']['options'] == list(db_models.BasicChoiceFieldModel.COLOR_CHOICES)


def test_datetime_format_settings(db_models, data_model_obj):
    DATETIME_FORMAT_SETTINGS = '%d/%m/%y'
    MARSHMALLOW_SETTINGS = {
        'DATETIME_FORMAT': DATETIME_FORMAT_SETTINGS
    }

    with override_settings(MARSHMALLOW_SETTINGS=MARSHMALLOW_SETTINGS):
        class TestSchema(ModelSchema):
            class Meta:
                model = db_models.DataFieldsModel
                fields = ('datetime_field',)

        schema = TestSchema()
        data = schema.dump(data_model_obj)
        assert len(data) == 1
        assert data['datetime_field'] == data_model_obj.datetime_field.strftime("%d/%m/%y")
