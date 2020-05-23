import typing
from collections.abc import Mapping as _Mapping

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
        'related_object_does_not_exists': 'Entity could not found on {field_name} for value: {value!r}'
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

        self.related_value_field = related_value_field
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
        value = self.related_value_field.deserialize(value, attr, data)

        if self.many and isinstance(value, (list, tuple)):
            data = []
            for pk in value:
                try:
                    data.append(self.related_model._default_manager.get(pk=pk))
                except ObjectDoesNotExist:
                    raise self.make_error(
                        'related_object_does_not_exists',
                        field_name=self.name,
                        value=value
                    )
            return data
        if self.to_field:
            try:
                return self.related_model._default_manager.get(pk=value)
            except ObjectDoesNotExist:
                raise self.make_error(
                    'related_object_does_not_exists',
                    field_name=self.name,
                    value=value
                )
        return super()._deserialize(value, attr, data, **kwargs)


class RelatedField(ma.fields.Dict):

    default_error_messages = {
        'invalid': '`RelatedField` data must be a {type} type.',
        'empty': '`RelatedField` data must be include a valid primary key value for {model_name} model.'
    }

    def __init__(self, keys=String, values=None, relation_info=None, many=False, **kwargs):
        super().__init__(keys, values, **kwargs)
        self.related_model = getattr(relation_info, 'related_model', None)
        self.many = many
        if not self.related_model:
            raise ma.exceptions.MarshmallowError(
                'RelatedNested needs to use with a inherited class of '
                '"ModelSchema" or can use with a Marshmallow "Schema" class implementation along with'
                ' `related_model` parameter.'
            )

    def _deserialize(self, value, attr, data, **kwargs):
        if not self.many and not isinstance(value, _Mapping):
            raise self.make_error('invalid', type=_Mapping.__name__)
        if self.many and not isinstance(value, list):
            raise self.make_error('invalid', type=list.__name__)

        if len(value) == 0:
            raise self.make_error('empty', model_name=self.related_model.__name__)

        if not self.many:
            errors = dict()
            result = dict()
            keys = {k: k for k in value.keys()}
            for key, val in value.items():
                try:
                    deser_val = self.value_field.deserialize(val, **kwargs)
                except ValidationError as error:
                    errors[key] = error.messages
                    if error.valid_data is not None and key in keys:
                        result[keys[key]] = error.valid_data
                else:
                    if key in keys:
                        result[keys[key]] = deser_val
        else:
            errors = list()
            result = list()
            for item in value:
                item_data = dict()
                for key, val in item.items():
                    keys = {k: k for k in item.keys()}
                    try:
                        deser_val = self.value_field.deserialize(val, **kwargs)
                    except ValidationError as error:
                        errors.append({key: error.messages})
                        if error.valid_data is not None and key in keys:
                            item_data[keys[key]] = error.valid_data
                    else:
                        if key in keys:
                            result[keys[key]] = deser_val

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
