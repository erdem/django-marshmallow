import typing
from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import marshmallow as ma
from django.utils.text import capfirst
from marshmallow import validate
from rest_framework.utils.field_mapping import get_relation_kwargs

from django_marshmallow.utils import get_field_info


class FileField(ma.fields.Inferred):
    pass


class ImageField(ma.fields.Inferred):
    pass


class SlugField(ma.fields.Inferred):
    pass


class IPAddress(ma.fields.Inferred):
    pass


class FilePath(ma.fields.Inferred):
    pass

class RelatedField(ma.fields.Field):

    default_error_messages = {
        "invalid": "Could not deserialize related value {value!r}; "
        "expected a dictionary with keys {keys!r}"
    }

    def __init__(
            self,
            model_field=None,
            related_model=None,
            to_many=None,
            to_field=None,
            has_through_model=None,
            reverse=None,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.model_field = model_field
        self.related_model = related_model
        self.to_many = to_many
        self.to_field = to_field
        self.has_through_model = has_through_model
        self.reverse = reverse

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if self.reverse:  # FixMe
            return "REVERSE"
        if self.to_many:
            value = list(value.values_list('pk', flat=True))
        if self.to_field:
            value = getattr(value, self.to_field)
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value: typing.Any, attr: str = None, data: typing.Mapping[str, typing.Any] = None, **kwargs):
        if self.reverse:  # FixMe
            return "REVERSE"
        if self.to_many and isinstance(value, list):
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

class ModelFieldConverter:
    """
    Class that converts a Django model into a dictionary of corresponding
    marshmallow `Fields <marshmallow.fields.Field>`.
    """

    SCHEMA_FIELD_MAPPING = {
        models.AutoField: ma.fields.Integer,
        models.BigIntegerField: ma.fields.Integer,
        models.BooleanField: ma.fields.Boolean,
        models.CharField: ma.fields.String,
        models.CommaSeparatedIntegerField: ma.fields.String,
        models.DateField: ma.fields.Date,
        models.DateTimeField: ma.fields.DateTime,
        models.DecimalField: ma.fields.Decimal,
        models.EmailField: ma.fields.Email,
        models.Field: ma.fields.Inferred,
        models.FileField: FileField,
        models.FloatField: ma.fields.Float,
        models.ImageField: ImageField,
        models.IntegerField: ma.fields.Integer,
        models.NullBooleanField: ma.fields.Boolean,
        models.PositiveIntegerField: ma.fields.Integer,
        models.PositiveSmallIntegerField: ma.fields.Integer,
        models.SlugField: SlugField,
        models.SmallIntegerField: ma.fields.Integer,
        models.TextField: ma.fields.String,
        models.TimeField: ma.fields.Time,
        models.URLField: ma.fields.URL,
        models.IPAddressField: IPAddress,
        models.GenericIPAddressField: IPAddress,
        models.FilePathField: FilePath,
        models.DurationField: ma.fields.TimeDelta,
    }

    related_field = RelatedField

    def __init__(self, schema_cls=None):
        self.schema_cls = schema_cls

    @property
    def type_mapping(self):
        if self.schema_cls:
            return self.schema_cls.TYPE_MAPPING
        else:
            return ma.Schema.TYPE_MAPPING

    def is_supported_model_field(self, model_field):
        return model_field.__class__ in self.SCHEMA_FIELD_MAPPING

    def fields_for_model(
        self,
        model,  # fixme there are too many paramaters here
        klass,
        *,
        include_fk=False,
        include_relationships=False,
        fields=None,
        exclude=None,
        base_fields=None,
        dict_cls=dict,
    ):
        opts = klass.opts
        nested_level = opts.level
        model = opts.model
        fields = opts.fields
        exclude = opts.exclude
        model_field_info = get_field_info(model)
        field_list = []
        ignored = []
        for field_name, model_field in model_field_info.all_fields.items():
            if fields is not None and field_name not in fields:
                continue
            if exclude and field_name in exclude:
                continue

            relation_info = model_field_info.relations.get(field_name)
            if relation_info and not relation_info.reverse:
                if nested_level:
                    model_schema_field = self.build_nested_field(
                        klass,
                        field_name,
                        relation_info,
                        nested_level
                    )
                else:
                    model_schema_field = self.build_relational_field(
                        klass,
                        field_name,
                        relation_info
                    )
                field_list.append(model_schema_field)
                continue

            if self.is_supported_model_field(model_field):
                model_schema_field = self.build_standard_field(field_name, model_field)
                field_list.append(model_schema_field)
            else:
                ignored.append((field_name, model_field))

        field_dict = OrderedDict(field_list)
        return field_dict

    def build_standard_field(self, field_name, model_field):
        field_class = self.SCHEMA_FIELD_MAPPING.get(model_field.__class__)
        field_kwargs = self.get_schema_field_kwargs(model_field)
        return field_name, field_class(**field_kwargs)

    def build_nested_field(self, new_class, field_name, relation_info, nested_level):
        class NestedSerializer(new_class):
            class Meta:
                model = relation_info.related_model
                fields = '__all__'
                level = nested_level - 1
        field_kwargs = self.get_schema_field_kwargs(relation_info.model_field)
        field_kwargs['many'] = relation_info.to_many
        field_class = ma.fields.Nested(NestedSerializer, **field_kwargs)
        return field_name, field_class

    def build_relational_field(self, klass, field_name, relation_info):
        field_class = self.related_field
        model_field, related_model, to_many, to_field, has_through_model, reverse = relation_info
        field_kwargs = self.get_schema_field_kwargs(model_field)
        field_kwargs['model_field'] = model_field
        field_kwargs['related_model'] = related_model
        field_kwargs['to_many'] = to_many
        field_kwargs['to_field'] = to_field
        field_kwargs['has_through_model'] = has_through_model
        field_kwargs['reverse'] = reverse
        return field_name, field_class(**field_kwargs)

    def get_schema_field_kwargs(self, model_field):
        kwargs = {}
        metadata = {}
        validator_kwarg = list(model_field.validators)
        kwargs['model_field'] = model_field

        if model_field.primary_key and not +model_field.editable:
            kwargs['dump_only'] = True

        if model_field.has_default() or model_field.blank or model_field.null:
            kwargs['required'] = False
        else:
            kwargs['required'] = True

        if model_field.verbose_name:
            metadata['label'] = capfirst(model_field.verbose_name)

        if model_field.help_text:
            metadata['help_text'] = model_field.help_text

        if model_field.blank and (isinstance(model_field, (models.CharField, models.TextField))):
            metadata['allow_blank'] = True

        if model_field.null and not isinstance(model_field, models.NullBooleanField):
            kwargs['allow_none'] = True

        if model_field.choices:
            validator_kwarg.append(validate.OneOf(choices=model_field.choices))

        kwargs['metadata'] = metadata
        return kwargs