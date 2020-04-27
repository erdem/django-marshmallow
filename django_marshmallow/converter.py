import typing
from collections import OrderedDict

from django.db import models

import marshmallow as ma
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
        # if self.reverse:
        #     return "REVERSE"
        if self.to_many:
            value = list(value.values_list('pk', flat=True))
        if self.to_field:
            value = getattr(value, self.to_field)
        return super()._serialize(value, attr, obj, **kwargs)


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

    # if ModelDurationField is not None:
    #     serializer_field_mapping[ModelDurationField] = DurationField
    # serializer_related_field = PrimaryKeyRelatedField
    # serializer_related_to_field = SlugRelatedField
    # serializer_url_field = HyperlinkedIdentityField
    # serializer_choice_field = ChoiceField

    DIRECTION_MAPPING = {
        'MANY_TO_ONE': False,
        'MANY_TO_MANY': True,
        'ONE_TO_MANY': True
    }

    def __init__(self, schema_cls=None):
        self.schema_cls = schema_cls

    @property
    def type_mapping(self):
        if self.schema_cls:
            return self.schema_cls.TYPE_MAPPING
        else:
            return ma.Schema.TYPE_MAPPING

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
        for field_name, field in model_field_info.all_fields.items():
            if fields is not None and field_name not in fields:
                continue
            if exclude and field_name in exclude:
                continue

            relation_info = model_field_info.relations.get(field_name)
            if relation_info:
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

            field_class = self.SCHEMA_FIELD_MAPPING.get(field.__class__)
            if field_class:
                model_schema_field = self.build_field(field_name, field_class)
                field_list.append(model_schema_field)
            else:
                ignored.append((field_name, field))

        field_dict = OrderedDict(field_list)
        return field_dict

    def build_field(self, field_name, model_schema_field, **field_kwargs):
        return field_name, model_schema_field(**field_kwargs)

    def build_nested_field(self, new_class, field_name, relation_info, nested_level, **field_kwargs):
        class NestedSerializer(new_class):
            class Meta:
                model = relation_info.related_model
                fields = '__all__'
                level = nested_level - 1
        field_kwargs['many'] = relation_info.to_many
        field_class = ma.fields.Nested(NestedSerializer, **field_kwargs)
        return field_name, field_class

    def build_relational_field(self, klass, field_name, relation_info):
        field_class = self.related_field
        model_field, related_model, to_many, to_field, has_through_model, reverse = relation_info
        return field_name, field_class(model_field, related_model, to_many, to_field, has_through_model, reverse)
