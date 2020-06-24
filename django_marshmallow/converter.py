from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.text import capfirst

from django_marshmallow import fields, schemas
from django_marshmallow.utils import get_field_info


class ModelFieldConverter:
    """
    Class that converts a Django model into a dictionary of corresponding
    marshmallow fields
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

    choice_field_class = fields.ChoiceField

    related_pk_field_class = fields.RelatedPKField
    related_field_class = fields.RelatedField
    related_nested_class = fields.RelatedNested

    def __init__(self, schema_cls, dict_cls=dict):
        self.schema_cls = schema_cls
        self.opts = schema_cls.opts
        self.dict_cls = dict_cls

    def is_standard_field(self, model_field):
        return model_field.__class__ in self.SCHEMA_FIELD_MAPPING

    def fields_for_model(self, declared_fields=None):
        model = self.opts.model
        schema_fields = self.opts.fields
        schema_nested_fields = self.opts.nested_fields
        exclude = self.opts.exclude
        nested_depth = self.opts.depth

        if not declared_fields:
            declared_fields = ()

        model_field_info = get_field_info(model)
        field_list = []

        for field_name, model_field in model_field_info.all_fields.items():

            if field_name in declared_fields:
                continue

            if schema_fields is not None and field_name not in schema_fields:
                continue

            if exclude and field_name in exclude:
                continue

            relation_info = model_field_info.relations.get(field_name)
            if relation_info:
                if relation_info.reverse:  # todo: support reverse relations
                    continue

                if field_name in schema_nested_fields:
                    model_schema_field = self.build_related_nested_field(
                        field_name,
                        model_field_info
                    )
                elif nested_depth:
                    model_schema_field = self.build_related_nested_field_with_depth(
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

    def get_schema_field_class(self, model_field):
        if model_field.choices:
            return self.choice_field_class
        return self.SCHEMA_FIELD_MAPPING.get(model_field.__class__)

    def build_standard_field(self, field_name, model_field):
        field_class = self.get_schema_field_class(model_field)
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

    def build_related_nested_field(self, field_name, model_field_info):
        relation_info = model_field_info.relations.get(field_name)

        if isinstance(self.opts.nested_fields, (list, tuple)):
            related_schema_class = schemas.modelschema_factory(
                model=relation_info.related_model,
                fields='__all__'
            )
        elif isinstance(self.opts.nested_fields, dict):
            nested_serializer_opts = self.opts.nested_fields.get(field_name)
            related_schema_class = schemas.modelschema_factory(
                model=relation_info.related_model,
                **nested_serializer_opts
            )
        else:
            raise ImproperlyConfigured(
                f'Invalid type `nested_fields` configuration for {field_name} field.'
            )

        field_kwargs = self.get_related_field_kwargs(relation_info)
        field_class = self.related_nested_class(related_schema_class, **field_kwargs)
        return field_name, field_class

    def build_related_nested_field_with_depth(self, field_name, model_field_info, nested_depth):
        relation_info = model_field_info.relations.get(field_name)
        related_schema_depth = nested_depth - 1
        related_schema_class = schemas.modelschema_factory(
            relation_info.related_model,
            fields=schemas.ALL_FIELDS,
            depth=related_schema_depth
        )
        field_kwargs = self.get_related_field_kwargs(relation_info)
        field_class = self.related_nested_class(related_schema_class, **field_kwargs)
        return field_name, field_class

    def build_related_field(self, field_name, model_field_info):
        relation_info = model_field_info.relations.get(field_name)
        field_kwargs = self.get_related_field_kwargs(relation_info)

        if not self.opts.expand_related_pk_fields:
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
        field_kwargs['related_pk_value_field'] = related_value_field
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
        field_validators = list(model_field.validators)
        kwargs['model_field'] = model_field

        if model_field.primary_key:
            kwargs['required'] = False
            return kwargs

        if not model_field.blank or not model_field.null:
            kwargs['required'] = True

        if model_field.null:
            kwargs['allow_none'] = True

        if model_field.validators:
            kwargs['validate'] = model_field.validators

        if not model_field.editable:
            kwargs['dump_only'] = True

        if model_field.blank and (isinstance(model_field, (models.CharField, models.TextField))):
            kwargs['allow_blank'] = True

        if model_field.null and not isinstance(model_field, models.NullBooleanField):
            kwargs['allow_none'] = True

        if model_field.verbose_name:
            kwargs['label'] = capfirst(model_field.verbose_name)

        if model_field.help_text:
            kwargs['help_text'] = model_field.help_text

        if model_field.choices:
            kwargs['choices'] = model_field.choices

        kwargs['validate'] = field_validators
        _django_form_field_kwargs = {
            'required': kwargs.get('required'),
            'label': kwargs.get('label'),
            'help_text': kwargs.get('help_text'),
            'validators': field_validators,
        }
        kwargs['_django_form_field_kwargs'] = _django_form_field_kwargs
        kwargs['field_kwargs'] = kwargs.copy()
        return kwargs
