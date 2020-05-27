import typing

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import marshmallow as ma
from marshmallow import ValidationError
from marshmallow.fields import *


class InferredField(ma.fields.Inferred):

    def __init__(self, **kwargs):
        self.model_field = kwargs.get('model_field')
        super().__init__()

    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(value, attr, obj, **kwargs)


class FileField(InferredField):
    pass


class ImageField(InferredField):
    pass


class BinaryField(InferredField):
    pass


class CommaSeparatedIntegerField(InferredField):
    pass


class FilePathField(InferredField):
    pass


class GenericIPAddressField(InferredField):
    pass


class IPAddressField(InferredField):
    pass


class SlugField(InferredField):
    pass


class RelatedPKField(ma.fields.Field):

    default_error_messages = {
        'related_object_does_not_exists': '`{field_name}` related field entity does not exists for "{value}" on {related_model}',
        'invalid_value': 'Related primary key value cannot be None'
    }

    def __init__(
            self,
            related_value_field,
            model_field,
            related_model,
            to_field,
            many,
            has_through_model,
            **kwargs
    ):
        super().__init__(**kwargs)
        if not many:
            self.related_value_field = related_value_field
        else:
            self.related_value_field = ma.fields.List(related_value_field)
        self.model_field = model_field
        self.related_model = related_model
        self.to_field = to_field
        self.many = many
        self.has_through_model = has_through_model
        self._field_cache = {}

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if self.many and isinstance(value, models.Manager):
            value = list(value.values_list('pk', flat=True))
        if self.many and isinstance(value, list):
            value = [v.id for v in value if isinstance(v, self.related_model)]
        if self.to_field:
            value = getattr(value, self.to_field)

        field_cls = self.root.TYPE_MAPPING.get(type(value))
        if field_cls is None:
            field = super()
        else:
            field = self._field_cache.get(field_cls)
            if field is None:
                field = field_cls()
                self._field_cache[field_cls] = field
        return field._serialize(value, attr, obj, **kwargs)

    def _validate(self, value):
        if self.many and not isinstance(value, (list, tuple)):
            raise ValidationError('ManytoMany fields values must be `list` or `tuple`')
        return super()._validate(value)

    def _deserialize(self, value, attr = None, data = None, **kwargs):
        if value is None:
            raise self.make_error('invalid_value')
        value = self.related_value_field.deserialize(value, attr, data)

        if self.many and isinstance(value, (list, tuple)):
            invalid_pks = []
            data = []
            for pk in value:
                try:
                    data.append(self.related_model._default_manager.get(pk=pk))
                except ObjectDoesNotExist:
                    invalid_pks.append(pk)

            if invalid_pks:
                raise self.make_error(
                    'related_object_does_not_exists',
                    field_name=self.model_field.name,
                    value=', '.join('{0}'.format(n) for n in invalid_pks),
                    related_model=self.related_model.__name__
                )
            return data

        if self.to_field:
            try:
                return self.related_model._default_manager.get(pk=value)
            except ObjectDoesNotExist:
                raise self.make_error(
                    'related_object_does_not_exists',
                    field_name=self.model_field.name,
                    value=str(value),
                    related_model=self.related_model.__name__
                )
        return super()._deserialize(value, attr, data, **kwargs)


class RelatedField(ma.fields.Field):

    default_error_messages = {
        'invalid': '`RelatedField` data must be a {type} type.',
        'empty': '`RelatedField` data must be include a valid primary key value for {model_name} model.',
        'too_many_pk': 'Received too many primary key values for single related field.',
        'invalid_keys': 'Received invalid data key(`{invalid_key}`) for `{field_name}` field. The related data key must be `{field_name}` or `pk`',
    }

    def __init__(self, related_pk_field=RelatedPKField, target_field=None, relation_info=None, many=False, **kwargs):
        super().__init__(**kwargs)
        self.related_model = getattr(relation_info, 'related_model', None)
        self.to_field = relation_info.to_field
        self.target_field = target_field
        self.many = many
        self.collection_type = list if many else dict
        self.value_field = related_pk_field
        if not self.related_model:
            raise ma.exceptions.MarshmallowError(
                'RelatedNested needs to use with a inherited class of '
                '"ModelSchema" or can use with a Marshmallow "Schema" class implementation along with'
                ' `related_model` parameter.'
            )

    def _deserialize(self, value, attr, data, **kwargs):
        if not self.many and not isinstance(value, dict):
            raise self.make_error('invalid', type=dict.__name__)
        if not self.many and len(value) > 1:
            raise self.make_error('too_many_pk')

        if self.many and not isinstance(value, list):
            raise self.make_error('invalid', type=list.__name__)

        if len(value) == 0:
            raise self.make_error('empty', model_name=self.related_model.__name__)

        result = self.collection_type()
        errors = self.collection_type()

        if not self.many:
            data_key = self.target_field if self.target_field in value else 'pk' if 'pk' in value else None
            if data_key is None:
                raise self.make_error(
                    'invalid_keys',
                    field_name=self.target_field,
                    invalid_key=list(value.keys())[0],
                )
            related_pk_value = value.get(data_key)
            try:
                deser_val = self.value_field.deserialize(related_pk_value, **kwargs)
            except ValidationError as error:
                errors[data_key] = error.messages
            else:
                result[data_key] = deser_val
        else:
            related_pk_values = []
            for item in value:
                data_key = self.target_field if self.target_field in item else 'pk' if 'pk' in item else None
                if data_key is None:
                    raise self.make_error(
                        'invalid_keys',
                        field_name=self.target_field,
                        invalid_key=list(item.keys())[0],
                    )
                related_pk_values.append(item.get(data_key))

            try:
                deser_val = self.value_field.deserialize(related_pk_values, **kwargs)
            except ValidationError as error:
                errors.append({data_key: error.messages})
            else:
                result.append({data_key: deser_val})

        if errors:
            raise ValidationError(errors, valid_data=result)

        return result


class RelatedNested(ma.fields.Nested):

    def __init__(self, nested, **kwargs):
        super().__init__(nested, **kwargs)
        self.related_model = kwargs.get('related_model', getattr(nested.opts, 'model', None))
        if not self.related_model:
            raise ma.exceptions.MarshmallowError(
                'RelatedNested needs to use with a inherited class of '
                '"ModelSchema" or can use with a Marshmallow "Schema" class implementation along with'
                ' `related_model` parameter.'
            )

    def deserialize(self, value, attr=None, data=None, **kwargs):
        data = super().deserialize(value, attr, data, **kwargs)
        if self.many:
            instance = [self.related_model(**d) for d in data]
        else:
            instance = self.related_model(**data)
        return instance
