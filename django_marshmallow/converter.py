from django.db import models
from django.utils.text import capfirst

from marshmallow import validate

from django_marshmallow import fields
from django_marshmallow.utils import get_field_info


class ModelFieldConverter:
    """
    Class that converts a Django model into a dictionary of corresponding
    marshmallow `Fields <marshmallow.fields.Field>`.
    """

    SCHEMA_FIELD_MAPPING = {
        models.AutoField: fields.Integer,
        models.BigAutoField: fields.Integer,
        models.BigIntegerField: fields.Integer,
        models.BinaryField: fields.BinaryField,
        models.BooleanField: fields.Boolean,
        models.CharField: fields.String,
        models.CommaSeparatedIntegerField: fields.CommaSeparatedIntegerField,
        models.DateField: fields.Date,
        models.DateTimeField: fields.DateTime,
        models.DecimalField: fields.Decimal,
        models.DurationField: fields.TimeDelta,
        models.EmailField: fields.Email,
        models.FilePathField: fields.FilePathField,
        models.FileField: fields.FileField,
        models.FloatField: fields.Float,
        models.GenericIPAddressField: fields.GenericIPAddressField,
        models.IPAddressField: fields.IPAddressField,
        models.ImageField: fields.ImageField,
        models.IntegerField: fields.Integer,
        models.NullBooleanField: fields.Boolean,
        models.PositiveIntegerField: fields.Integer,
        models.PositiveSmallIntegerField: fields.Integer,
        models.SlugField: fields.String,
        models.SmallIntegerField: fields.Integer,
        models.TextField: fields.String,
        models.TimeField: fields.Time,
        models.URLField: fields.URL,
        models.UUIDField: fields.UUID,
    }

    related_pk_field_class = fields.RelatedPKField
    related_field_class = fields.RelatedField
    related_nested_class = fields.RelatedNested

    def __init__(self, schema_cls, dict_cls=dict):
        self.schema_cls = schema_cls
        self.opts = schema_cls.opts
        self.dict_cls = dict_cls
        self._is_related_field_schema = self.opts._related_field_schema

    def is_standard_field(self, model_field):
        return model_field.__class__ in self.SCHEMA_FIELD_MAPPING

    def fields_for_model(self):
        model = self.opts.model
        schema_fields = self.opts.fields
        exclude = self.opts.exclude
        include_pk = self.opts.include_pk
        nested_depth = self.opts.depth

        model_field_info = get_field_info(model)
        field_list = []

        if include_pk:
            pk_field = self.build_primary_key_field(
                field_name=self.schema_cls.model_pk_field.name,
                model_field=self.schema_cls.model_pk_field
            )
            field_list.append(pk_field)
        for field_name, model_field in model_field_info.all_fields.items():

            if schema_fields is not None and field_name not in schema_fields:
                continue

            if exclude and field_name in exclude:
                continue

            if field_name == self.schema_cls.model_pk_field.name:
                continue

            relation_info = model_field_info.relations.get(field_name)
            if relation_info:
                if relation_info.reverse:
                    continue

                if nested_depth:
                    model_schema_field = self.build_related_nested_field(
                        field_name,
                        model_field_info,
                        nested_depth
                    )
                else:
                    model_schema_field = self.build_related_field(
                        field_name,
                        model_field_info
                    )
                field_list.append(model_schema_field)
                continue

            if self.is_standard_field(model_field):
                model_schema_field = self.build_standard_field(field_name, model_field)
            else:
                model_schema_field = self.build_inferred_field(field_name, model_field)
            field_list.append(model_schema_field)

        return self.dict_cls(field_list)

    def build_standard_field(self, field_name, model_field):
        field_class = self.SCHEMA_FIELD_MAPPING.get(model_field.__class__)
        field_kwargs = self.get_schema_field_kwargs(model_field)
        return field_name, field_class(**field_kwargs)

    def build_primary_key_field(self, field_name, model_field):
        field_class = self.SCHEMA_FIELD_MAPPING.get(model_field.__class__)
        field_kwargs = self.get_schema_field_kwargs(model_field)
        return field_name, field_class(**field_kwargs)

    def build_inferred_field(self, field_name, model_field):
        """
        Return a `InferredField` for third party or custom model fields
        """
        field_kwargs = self.get_schema_field_kwargs(model_field)
        return field_name, fields.InferredField(**field_kwargs)

    def build_related_nested_field(self, field_name, model_field_info, nested_depth):
        from django_marshmallow.schemas import ModelSchema

        relation_info = model_field_info.relations.get(field_name)

        class RelatedModelSerializer(ModelSchema):  # Fixme: rid of this
            class Meta:
                model = relation_info.related_model
                fields = '__all__'
                depth = nested_depth - 1

        field_kwargs = self.get_related_field_kwargs(relation_info)
        field_class = self.related_nested_class(RelatedModelSerializer, **field_kwargs)
        return field_name, field_class

    def build_related_field(self, field_name, model_field_info):
        relation_info = model_field_info.relations.get(field_name)
        field_kwargs = self.get_related_field_kwargs(relation_info)
        if self.opts.use_related_pk_fields:
            field_class = self.related_pk_field_class(**field_kwargs)
        else:
            related_pk_field = self.related_pk_field_class(**field_kwargs)
            field_kwargs['related_pk_field'] = related_pk_field
            field_class = self.related_field_class(**field_kwargs)
        return field_name, field_class

    def get_related_field_kwargs(self, relation_info):
        model_field, related_model, to_many, to_field, has_through_model, reverse = relation_info
        related_target_name, related_value_field = self.build_standard_field(
            to_field, related_model._meta.pk
        )
        field_kwargs = self.get_schema_field_kwargs(model_field)
        field_kwargs['related_value_field'] = related_value_field
        queryset = related_model._default_manager
        field_kwargs['queryset'] = queryset

        limit_choices_to = model_field and model_field.get_limit_choices_to()
        if limit_choices_to:
            if not isinstance(limit_choices_to, models.Q):
                limit_choices_to = models.Q(**limit_choices_to)
            field_kwargs['queryset'] = queryset.filter(limit_choices_to)

        if has_through_model:
            field_kwargs['dump_only'] = True
            field_kwargs.pop('queryset', None)

        if not model_field.editable:
            field_kwargs['dump_only'] = True
            field_kwargs.pop('queryset', None)

        field_kwargs['model_field'] = model_field
        field_kwargs['related_model'] = related_model
        field_kwargs['many'] = to_many
        field_kwargs['target_field'] = related_model._meta.pk.name
        field_kwargs['to_field'] = to_field
        field_kwargs['has_through_model'] = has_through_model
        field_kwargs['relation_info'] = relation_info
        return field_kwargs

    def get_schema_field_kwargs(self, model_field):
        kwargs = {}
        metadata = {}
        validator_kwarg = list(model_field.validators)
        kwargs['model_field'] = model_field

        if model_field.primary_key and not self._is_related_field_schema:
            kwargs['required'] = False
            return kwargs

        if not model_field.blank or not model_field.null:
            kwargs['required'] = True  # required=False for all fields by default on marshmallow
        if model_field.null:
            kwargs['allow_none'] = True
        if model_field.validators:
            kwargs['validate'] = model_field.validators
        if not model_field.editable:
            kwargs['dump_only'] = True

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
