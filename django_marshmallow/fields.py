import typing

from django.core.exceptions import ObjectDoesNotExist

import marshmallow as ma
from marshmallow.fields import *


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
        self.to_field = kwargs.get('to_field')
        self.many = kwargs.get('many', False)
        self.has_through_model = kwargs.get('has_through_model', False)
        self.is_reverse_relation = kwargs.get('is_reverse_relation', False)

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if self.is_reverse_relation:  # FixMe
            return "REVERSE"
        # if self.many and isinstance(value, list):
        #     value = [v.pk for v in value if isinstance(v, self.related_model)]
        # if self.many and isinstance(value, models.Manager):
        #     value = list(value.values_list('pk', flat=True))
        # if self.to_field:
        #     value = getattr(value, self.to_field)
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


class RelatedPKField(ma.fields.Field):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_field = kwargs.get('model_field')
        self.to_field = kwargs.get('to_field')
        self.many = kwargs.get('many', False)
        self.has_through_model = kwargs.get('has_through_model', False)
        self.is_reverse_relation = kwargs.get('is_reverse_relation', False)

    def _serialize(self, value, attr, obj, **kwargs):
        field_cls = self.root.TYPE_MAPPING.get(type(value))
        if field_cls is None:
            field = super()
        else:
            field = self._field_cache.get(field_cls)
            if field is None:
                field = field_cls()
                field._bind_to_schema(self.name, self.parent)
                self._field_cache[field_cls] = field
        return field._serialize(value, attr, obj, **kwargs)

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
