import uuid

import pytest

from django_marshmallow.schemas import ModelSchema


@pytest.fixture
def fk_related_instance(db_models):
    foreign_key_instnace = db_models.ForeignKeyTarget(
        name='Foreign Key'
    )
    foreign_key_instnace.save()
    return foreign_key_instnace


@pytest.fixture
def m2m_related_instance(db_models):
    many_to_many_instance = db_models.ManyToManyTarget(
        name='Many to Many'
    )
    many_to_many_instance.save()
    return many_to_many_instance


@pytest.fixture
def o2o_related_instance(db_models):
    one_to_one_instance = db_models.OneToOneTarget(
        name='One to One'
    )
    one_to_one_instance.save()
    return one_to_one_instance


def test_invalid_primary_key_validation_for_foreign_key_fields(db, db_models):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('foreign_key_field', )

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'foreign_key_field': {
            'id': 'INVALID STRING ID'
        }
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field']['id'] == ['Not a valid integer.']

    load_data = {
        'foreign_key_field': 'INVALID TYPE'
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == ['`RelatedField` data must be a dict type.']

    load_data = {
        'foreign_key_field': {}
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == [
        '`RelatedField` data must be include a valid primary key value for ForeignKeyTarget model.'
    ]

    load_data = {
        'foreign_key_field': {
            'id': '1'
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == {'id': [
        '`foreign_key_field` related field entity does not exists for "1" on ForeignKeyTarget'
    ]}

    load_data = {
        'foreign_key_field': {
            'pk': '1'
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == {'pk': [
        '`foreign_key_field` related field entity does not exists for "1" on ForeignKeyTarget'
    ]}


def test_invalid_primary_key_validation_for_many_to_many_fields(db, db_models):

    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('many_to_many_field', )

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'many_to_many_field': [
            {
                'id': 'INVALID KEY'
            },
            {
                'id': '1'
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [
        'Received invalid data key for related primary key. The related data key must be `uuid` or `pk`'
    ]

    load_data = {
        'many_to_many_field': [
            {
                'uuid': 'INVALID STRING UUID'
            },
            {
                'uuid': '1'
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'uuid': {0: ['Not a valid UUID.'], 1: ['Not a valid UUID.']}}]

    load_data = {
        'many_to_many_field': [
            {
                'pk': 'INVALID PK'
            },
            {
                'pk': '1'
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'pk': {0: ['Not a valid UUID.'], 1: ['Not a valid UUID.']}}]

    uuid_1 = uuid.uuid4()
    uuid_2 = uuid.uuid4()

    load_data = {
        'many_to_many_field': [
            {
                'uuid': uuid_1
            },
            {
                'uuid': uuid_2
            }
        ]
    }


    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'uuid': ['`many_to_many_field` related field entity does not exists for '
           f'"[UUID(\'{uuid_1}\'), '
           f'UUID(\'{uuid_2}\')]" on '
           'ManyToManyTarget']}]

    uuid_1 = str(uuid.uuid4())
    uuid_2 = str(uuid.uuid4())

    load_data = {
        'many_to_many_field': [
            {
                'pk': uuid_1
            },
            {
                'pk': uuid_2
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [{'pk': ['`many_to_many_field` related field entity does not exists for '
           f'"[UUID(\'{uuid_1}\'), '
           f'UUID(\'{uuid_2}\')]" on '
           'ManyToManyTarget']}]