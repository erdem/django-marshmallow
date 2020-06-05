import uuid

import pytest

from django_marshmallow import fields
from django_marshmallow.schemas import ModelSchema


@pytest.fixture
def fk_related_instance(db_models):
    foreign_key_instnace = db_models.ForeignKeyTarget(
        name='Foreign Key'
    )
    foreign_key_instnace.save()
    return foreign_key_instnace


@pytest.fixture
def m2m_related_instances(db_models):
    many_to_many_instance_1 = db_models.ManyToManyTarget(
        name='Many to Many 1'
    )
    many_to_many_instance_1.save()

    many_to_many_instance_2 = db_models.ManyToManyTarget(
        name='Many to Many 2'
    )
    many_to_many_instance_2.save()
    m2m_instances = [
        many_to_many_instance_1,
        many_to_many_instance_2
    ]
    return m2m_instances


@pytest.fixture
def o2o_related_instance(db_models):
    one_to_one_instance = db_models.OneToOneTarget(
        name='One to One'
    )
    one_to_one_instance.save()
    return one_to_one_instance


def test_invalid_primary_key_validation_for_foreign_key_fields(db, db_models, fk_related_instance):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('foreign_key_field',)

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    validate_data = {
        'foreign_key_field': {
            'id': 'INVALID STRING PK'
        }
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['foreign_key_field']['id'] == ['Not a valid integer.']

    validate_data = {
        'foreign_key_field': 'INVALID TYPE'
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == ['`RelatedField` data must be a dict type.']

    validate_data = {
        'foreign_key_field': {}
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == [
        '`RelatedField` data must be include a valid primary key value for ForeignKeyTarget model.'
    ]

    validate_data = {
        'foreign_key_field': {
            'id': '888'
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == {'id': [
        '`foreign_key_field` related field entity does not exists for "888" on ForeignKeyTarget'
    ]}

    validate_data = {
        'foreign_key_field': {
            'pk': '888'
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == {'pk': [
        '`foreign_key_field` related field entity does not exists for "888" on ForeignKeyTarget'
    ]}

    # test valid datas

    validate_data = {
        'foreign_key_field': {
            'pk': fk_related_instance.pk
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) == 0

    validate_data = {
        'foreign_key_field': {
            'id': fk_related_instance.pk
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) == 0


def test_invalid_primary_key_validation_for_many_to_many_fields(db, db_models, m2m_related_instances):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('many_to_many_field',)

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    validate_data = {
        'many_to_many_field': [
            {
                'invalid_key': 'INVALID KEY'
            },
            {
                'invalid_key': '1'
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [
        'Received invalid data key(`invalid_key`) for `uuid` field. The related data key must be `uuid` or `pk`'
    ]

    validate_data = {
        'many_to_many_field': [
            {
                'uuid': 'INVALID STRING UUID'
            },
            {
                'uuid': '1'
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'uuid': {0: ['Not a valid UUID.'], 1: ['Not a valid UUID.']}}]

    validate_data = {
        'many_to_many_field': [
            {
                'pk': 'INVALID PK'
            },
            {
                'pk': '1'
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'pk': {0: ['Not a valid UUID.'], 1: ['Not a valid UUID.']}}]

    uuid_1 = uuid.uuid4()
    uuid_2 = uuid.uuid4()

    validate_data = {
        'many_to_many_field': [
            {
                'uuid': uuid_1
            },
            {
                'uuid': uuid_2
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'uuid': ['`many_to_many_field` related field entity does not exists for '
                                                      f'"{uuid_1}, '
                                                      f'{uuid_2}" on ManyToManyTarget']}]

    uuid_1 = str(uuid.uuid4())
    uuid_2 = str(uuid.uuid4())

    validate_data = {
        'many_to_many_field': [
            {
                'pk': uuid_1
            },
            {
                'pk': uuid_2
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'pk': ['`many_to_many_field` related field entity does not exists for '
                                                    f'"{uuid_1}, '
                                                    f'{uuid_2}" on ManyToManyTarget']}]

    # test valid datas
    validate_data = {
        'many_to_many_field': [
            {
                'uuid': m2m_related_instances[0].pk
            },
            {
                'uuid': m2m_related_instances[1].pk
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) == 0

    validate_data = {
        'many_to_many_field': [
            {
                'pk': m2m_related_instances[0].pk
            },
            {
                'pk': m2m_related_instances[1].pk
            }
        ]
    }

    errors = schema.validate(validate_data)

    assert len(errors) == 0


def test_invalid_primary_key_validation_for_one_to_one_fields(db, db_models, o2o_related_instance):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('one_to_one_field',)

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    validate_data = {
        'one_to_one_field': {
            'uuid': 'INVALID STRING PK'
        }
    }

    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['one_to_one_field']['uuid'] == ['Not a valid UUID.']

    validate_data = {
        'one_to_one_field': 'INVALID TYPE'
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == ['`RelatedField` data must be a dict type.']

    validate_data = {
        'one_to_one_field': {}
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == [
        '`RelatedField` data must be include a valid primary key value for OneToOneTarget model.'
    ]

    # invalid key
    uuid_pk = uuid.uuid4()
    validate_data = {
        'one_to_one_field': {
            'invalid_key': uuid_pk
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == [
        'Received invalid data key(`invalid_key`) for `uuid` field. The related data key must be `uuid` or `pk`'
    ]

    validate_data = {
        'one_to_one_field': {
            'pk': uuid_pk
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == {'pk': ['`one_to_one_field` related field entity does not exists for '
                                                 f'"{uuid_pk}" on OneToOneTarget']}

    # test valid datas

    validate_data = {
        'one_to_one_field': {
            'pk': o2o_related_instance.pk
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) == 0

    validate_data = {
        'one_to_one_field': {
            'uuid': o2o_related_instance.uuid
        }
    }
    errors = schema.validate(validate_data)

    assert len(errors) == 0


def test_explicit_nested_schema_validations(db, db_models):
    class ForeignKeySchema(ModelSchema):
        class Meta:
            model = db_models.ForeignKeyTarget
            fields = ('id', 'name')

    class TestSchema(ModelSchema):
        foreign_key_field = fields.RelatedNested(ForeignKeySchema)

        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field')

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    validate_data = {
        'name': 'Nested Schema Test Name',
        'foreign_key_field': {
            'name': None
        }
    }

    schema = TestSchema()
    errors = schema.validate(validate_data)

    assert len(errors) > 0
    assert errors['foreign_key_field']['name'] == ['Field may not be null.']


def test_implicit_nested_fields_schema_validations(db, db_models):
    class TestFKSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'foreign_key_field')

            # `nested_fields` option auto generating nested schema
            nested_fields = ('foreign_key_field',)

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    validate_data = {
        'name': 'Nested Schema Test Name',
        'foreign_key_field': {
            'name': None
        }
    }

    schema = TestFKSchema()
    errors = schema.validate(validate_data)

    assert len(errors) == 1
    assert errors['foreign_key_field']['name'] == ['Field may not be null.']

    # more complex usage

    class TestM2MSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'many_to_many_field')

            # `nested_fields` option can include nested schema options
            nested_fields = {
                'many_to_many_field': {
                    'fields': ('uuid', 'name')
                }
            }

    uuid_pk = str(uuid.uuid4())
    validate_data = {
        'name': 'Nested Schema Test Name',
        'many_to_many_field': [
            {
                'uuid': uuid_pk,
                'name': None
            }
        ]
    }

    schema = TestM2MSchema()
    errors = schema.validate(validate_data)
    assert len(errors) == 1
    assert errors['many_to_many_field'] == {0: {'name': ['Field may not be null.']}}

    # `nested_fields` option can generate multi level nested schema field

    class TestM2MSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('name', 'many_to_many_field')

            nested_fields = {
                'many_to_many_field': {
                    'fields': ('uuid', 'name', 'second_depth_relation_field'),
                    'nested_fields': ('second_depth_relation_field', )
                }
            }

    uuid_pk = str(uuid.uuid4())
    validate_data = {
        'name': 'Nested Schema Test Name',
        'many_to_many_field': [
            {
                'uuid': uuid_pk,
                'name': 'M2M first level name',
                'second_depth_relation_field': {
                    'name': None
                }
            }
        ]
    }

    schema = TestM2MSchema()
    errors = schema.validate(validate_data)
    assert len(errors) == 1
    assert errors['many_to_many_field'] == {0: {'second_depth_relation_field': {'name': ['Field may not be null.']}}}


def test_string_allow_blank_validation(db_models):
    class TestSchema(ModelSchema):
        char_field = fields.String()

        class Meta:
            model = db_models.DataFieldsModel
            fields = ('char_field', 'text_field', 'text_field_blank_true')

    validate_data = {
        'char_field': '',
        'text_field': '',
        'text_field_blank_true': '',
    }
    schema = TestSchema()
    errors = schema.validate(validate_data)

    assert len(errors) == 2
    assert errors == {'char_field': ['Field cannot be blank'], 'text_field': ['Field cannot be blank']}
