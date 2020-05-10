import typing

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import marshmallow as ma


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

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        super()._deserialize(value, attr, data, partial, **kwargs)
        return self.schema.save()


class RelatedField(ma.fields.Field):

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

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if self.is_reverse_relation:  # FixMe
            return "REVERSE"
        if self.many and isinstance(value, models.Manager):
            value = list(value.values_list('pk', flat=True))
        if self.many and isinstance(value, list):
            value = [v.id for v in value if isinstance(v, self.related_model)]
        if self.to_field:
            value = getattr(value, self.to_field)
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value: typing.Any, attr: str = None, data: typing.Mapping[str, typing.Any] = None, **kwargs):
        if self.is_reverse_relation:  # FixMe
            return "REVERSE"
        if self.many and isinstance(value, list):
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


class InferredField(ma.fields.Inferred):

    def __init__(self, **kwargs):
        self.model_field = kwargs.get('model_field')
        super().__init__()


class FileField(InferredField):
    pass


class ImageField(InferredField):
    pass

