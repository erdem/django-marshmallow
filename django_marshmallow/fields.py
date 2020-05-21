import typing

from django.core.exceptions import ObjectDoesNotExist, ValidationError

import marshmallow as ma
from django.db import models
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
        "invalid": "Could not deserialize related value {value!r}; "
        "expected a dictionary with keys {keys!r}"
    }

    def __init__(
            self,
            model_field,
            related_model,
            to_field,
            many,
            has_through_model,
            is_reverse_relation,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.model_field = model_field
        self.related_model = related_model
        self.to_field = to_field
        self.many = many
        self.has_through_model = has_through_model
        self.is_reverse_relation = is_reverse_relation
        self._field_cache = {}

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if self.is_reverse_relation:  # FixMe
            return "REVERSE"
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

    def _deserialize(self, value: typing.Any, attr: str = None, data: typing.Mapping[str, typing.Any] = None, **kwargs):
        if self.is_reverse_relation:  # FixMe
            return "REVERSE"
        if self.many and isinstance(value, (list, tuple)):
            data = []
            for pk in value:
                try:
                    data.append(self.related_model._default_manager.get(pk=pk))
                except ObjectDoesNotExist:
                    self.make_error('invalid', value=value)
            return data
        if self.to_field:
            try:
                return self.related_model._default_manager.get(pk=value)
            except ObjectDoesNotExist:
                self.make_error('invalid', value=value)
        return super()._deserialize(value, attr, data, **kwargs)


class RelatedField(ma.fields.Nested):

    default_error_messages = {  # todo update error messages
        "invalid": "Could not deserialize related value {value!r}; "
        "expected a dictionary with keys {keys!r}"
    }

    def __init__(self, nested=None, relation_info=None, **kwargs):
        from django_marshmallow.schemas import ModelSchema

        if not nested:
            class NestedSerializer(ModelSchema):  # fixMe use `model_schema_factory` method
                class Meta:
                    model = relation_info.related_model
                    include_pk = True
                    _related_field_schema = True

            nested = NestedSerializer

        super().__init__(nested, **kwargs)
        self.related_model = kwargs.get('related_model', getattr(nested.opts, 'model', None))

        if not self.related_model:
            raise ma.exceptions.MarshmallowError(
                'RelatedNested needs to use with a inherited class of '
                '"ModelSchema" or can use with a Marshmallow "Schema" class implementation along with'
                ' `related_model` parameter.'
            )

        self.model_field = kwargs.get('model_field')
        self.to_field = relation_info.to_field
        self.many = kwargs.get('many', False)
        self.relation_info = relation_info
        self.is_reverse_relation = kwargs.get('is_reverse_relation', False)

    def _validate(self, value):
        return super()._validate(value)

    def _deserialize(self, value: typing.Any, attr: str = None, data: typing.Mapping[str, typing.Any] = None, **kwargs):
        cc = super()._deserialize(value, attr, data, **kwargs)

        if self.is_reverse_relation:  # FixMe
            return "REVERSE"
        if self.many and isinstance(value, list):
            data = []
            for pk in value:
                try:
                    data.append(self.related_model._default_manager.get(**pk))
                except ObjectDoesNotExist:
                    self.make_error('invalid', value=value)
            return data
        if self.to_field:
            try:
                return self.related_model._default_manager.get(**value)
            except ObjectDoesNotExist:
                self.make_error('invalid', value=value)
        return data


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

    def _load(self, value, data, partial=None):
        return super()._load(value, data, partial)

    def _deserialize(self, value: typing.Any, attr: str = None, data: typing.Mapping[str, typing.Any] = None, **kwargs):
        super()._deserialize(value, attr, data, **kwargs)
        return self.schema.save()
