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
            fields = ('foreign_key_field', )

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'foreign_key_field': {
            'id': 'INVALID STRING PK'
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
            'id': '888'
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == {'id': [
        '`foreign_key_field` related field entity does not exists for "888" on ForeignKeyTarget'
    ]}

    load_data = {
        'foreign_key_field': {
            'pk': '888'
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['foreign_key_field'] == {'pk': [
        '`foreign_key_field` related field entity does not exists for "888" on ForeignKeyTarget'
    ]}

    # test valid datas

    load_data = {
        'foreign_key_field': {
            'pk': fk_related_instance.pk
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) == 0

    load_data = {
        'foreign_key_field': {
            'id': fk_related_instance.pk
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) == 0


def test_invalid_primary_key_validation_for_many_to_many_fields(db, db_models, m2m_related_instances):

    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('many_to_many_field', )

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'many_to_many_field': [
            {
                'invalid_key': 'INVALID KEY'
            },
            {
                'invalid_key': '1'
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['many_to_many_field'] == [
        'Received invalid data key(`invalid_key`) for `uuid` field. The related data key must be `uuid` or `pk`'
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
           f'"{uuid_1}, '
           f'{uuid_2}" on ManyToManyTarget']}]

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
           f'"{uuid_1}, '
           f'{uuid_2}" on ManyToManyTarget']}]

    # test valid datas
    load_data = {
        'many_to_many_field': [
            {
                'uuid': m2m_related_instances[0].pk
            },
            {
                'uuid': m2m_related_instances[1].pk
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) == 0

    load_data = {
        'many_to_many_field': [
            {
                'pk': m2m_related_instances[0].pk
            },
            {
                'pk': m2m_related_instances[1].pk
            }
        ]
    }

    errors = schema.validate(load_data)

    assert len(errors) == 0


def test_invalid_primary_key_validation_for_one_to_one_fields(db, db_models, o2o_related_instance):
    class TestSchema(ModelSchema):
        class Meta:
            model = db_models.AllRelatedFieldsModel
            fields = ('one_to_one_field', )

    schema = TestSchema()

    assert db_models.AllRelatedFieldsModel.objects.count() == 0

    load_data = {
        'one_to_one_field': {
            'uuid': 'INVALID STRING PK'
        }
    }

    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['one_to_one_field']['uuid'] == ['Not a valid UUID.']

    load_data = {
        'one_to_one_field': 'INVALID TYPE'
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == ['`RelatedField` data must be a dict type.']

    load_data = {
        'one_to_one_field': {}
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == [
        '`RelatedField` data must be include a valid primary key value for OneToOneTarget model.'
    ]

    # invalid key
    uuid_pk = uuid.uuid4()
    load_data = {
        'one_to_one_field': {
            'invalid_key': uuid_pk
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == [
        'Received invalid data key(`invalid_key`) for `uuid` field. The related data key must be `uuid` or `pk`'
    ]

    load_data = {
        'one_to_one_field': {
            'pk': uuid_pk
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) > 0
    assert errors['one_to_one_field'] == {'pk': ['`one_to_one_field` related field entity does not exists for '
        f'"{uuid_pk}" on OneToOneTarget']}

    # test valid datas

    load_data = {
        'one_to_one_field': {
            'pk': o2o_related_instance.pk
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) == 0

    load_data = {
        'one_to_one_field': {
            'uuid': o2o_related_instance.uuid
        }
    }
    errors = schema.validate(load_data)

    assert len(errors) == 0
