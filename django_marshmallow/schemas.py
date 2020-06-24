import copy
import typing
from collections import OrderedDict
from itertools import chain

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.functional import cached_property
from marshmallow.fields import Field
from marshmallow.schema import SchemaMeta, SchemaOpts

from marshmallow import Schema, ValidationError

from django_marshmallow.converter import ModelFieldConverter
from django_marshmallow.fields import RelatedField, RelatedNested
from django_marshmallow.utils import construct_instance


ALL_FIELDS = '__all__'


class ModelSchemaOpts(SchemaOpts):

    def __init__(self, meta, ordered: bool = False):
        from django_marshmallow.settings import ma_settings

        fields = getattr(meta, 'fields', None)
        self.model = getattr(meta, 'model', None)

        # Bypass Marshmallow options class `fields` attribute validation for "__all__" option.
        if fields == ALL_FIELDS:
            meta.fields = ()
        super(ModelSchemaOpts, self).__init__(meta, ordered)
        if fields == ALL_FIELDS:
            self.fields = ALL_FIELDS

        self.nested_fields = getattr(meta, 'nested_fields', ())

        if not isinstance(self.nested_fields, (list, tuple, dict)):
            raise ValueError('`nested_fields` option must be a list, tuple or dict.')

        self.order_by = getattr(meta, 'order_by', ma_settings.ORDER_BY)
        if not isinstance(self.order_by, (list, tuple)):
            raise ValueError("`order_by` schema option must be a list or tuple.")

        self.error_message_overrides = getattr(meta, 'error_message_overrides', ma_settings.ERROR_MESSAGE_OVERRIDES)
        if self.error_message_overrides is not None and not isinstance(self.error_message_overrides, dict):
            raise ValueError('`error_message_overrides` option must be a dict.')

        if ma_settings.DATE_FORMAT:
            self.dateformat = ma_settings.DATE_FORMAT

        if ma_settings.DATETIME_FORMAT:
            self.datetimeformat = ma_settings.DATETIME_FORMAT

        if ma_settings.RENDER_MODULE:
            self.render_module = ma_settings.RENDER_MODULE

        if ma_settings.INDEX_ERRORS:
            self.index_errors = ma_settings.INDEX_ERRORS

        if ma_settings.LOAD_ONLY:
            self.load_only = ma_settings.LOAD_ONLY

        if ma_settings.DUMP_ONLY:
            self.dump_only = ma_settings.DUMP_ONLY

        if ma_settings.UNKNOWN_FIELDS_ACTION:
            self.unknown = ma_settings.UNKNOWN_FIELDS_ACTION

        self.model_converter = getattr(meta, 'model_converter', ModelFieldConverter)
        self.depth = getattr(meta, 'depth', None)
        self.ordered = getattr(meta, 'ordered', ma_settings.ORDERED)
        self.expand_related_pk_fields = getattr(meta, 'expand_related_pk_fields', ma_settings.EXPAND_RELATED_PK_FIELDS)
        self.show_select_options = getattr(meta, 'show_select_options', ma_settings.SHOW_SELECT_OPTIONS)
        self.use_file_url = getattr(meta, 'use_file_url', ma_settings.USE_FILE_URL)
        self.domain_for_file_urls = getattr(meta, 'domain_for_file_urls', ma_settings.DOMAIN_FOR_FILE_URLS)


class ModelSchemaMetaclass(SchemaMeta):

    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        _pk_field = None
        if klass._declared_fields:
            model_pk_field_name = klass.opts.model._meta.pk.name
            _pk_field = klass._declared_fields.get(model_pk_field_name)
        klass._pk_field = _pk_field
        return klass

    @classmethod
    def validate_schema_option_class(mcs, klass):
        opts = klass.opts
        fields = opts.fields
        exclude = opts.exclude
        model = opts.model

        if not model:
            raise ImproperlyConfigured(
                'Creating a ModelSchema without `Meta.model` attribute is prohibited; %s '
                'schema class needs updating.' % klass.__name__
            )

        if not isinstance(model, type) or not issubclass(model, models.Model):
            raise ImproperlyConfigured(
                '`model` option must be a Django model class'
            )

        if not fields and not exclude:
            raise ImproperlyConfigured(
                'Creating a ModelSchema without either `Meta.fields` attribute '
                'or `Meta.exclude` attribute is prohibited; %s '
                'schema class needs updating.' % klass.__name__
            )

        if fields and exclude:
            raise ImproperlyConfigured(
                f'Cannot set `fields` and `exclude` options both together on model schemas.'
                f'{klass.__class__.__name__} schema class needs updating.'
            )

        depth = opts.depth
        if depth is not None:
            assert depth >= 0, f'`depth` cannot be negative. {klass.__class__.__name__} schema class schema class needs updating.'
            assert depth <= 10, f'`depth` cannot be greater than 10. {klass.__class__.__name__} schema class schema class needs updating.'

    @property
    def model_pk_field(mcs):
        return mcs.opts.model._meta.pk

    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        """
        Overridden for updates declared schema fields with fields converted from the django model.
        """

        # no needs to declare fields for base structure classes
        if klass.__name__ in ('BaseModelSchema', 'ModelSchema'):
            return super().get_declared_fields(klass, cls_fields, inherited_fields, dict_cls)

        mcs.validate_schema_option_class(klass)
        opts = klass.opts
        if opts.fields == ALL_FIELDS:
            # Sentinel for `fields_for_model` to indicate "get the list of
            # fields from the model"
            opts.fields = None
        Converter=opts.model_converter
        converter = Converter(
            schema_cls=klass,
            dict_cls=dict_cls
        )
        declared_fields = super().get_declared_fields(
            klass, cls_fields, inherited_fields, dict_cls
        )
        fields = converter.fields_for_model(declared_fields)
        fields.update(declared_fields)
        return fields


class BaseModelSchema(Schema, metaclass=ModelSchemaMetaclass):
    OPTIONS_CLASS = ModelSchemaOpts

    @cached_property
    def model_class(self):
        return self.opts.model

    @cached_property
    def pk_field(self):
        return self._pk_field

    def get_fields(self):
        return copy.deepcopy(self._declared_fields)

    @cached_property
    def fields(self):
        return self.get_fields()

    @cached_property
    def related_fields(self):
        related_fields = []
        for field_name, field in self.fields.items():
            if isinstance(field, (RelatedField, RelatedNested)):
                related_fields.append((field_name, field))
        return OrderedDict(related_fields)

    @cached_property
    def related_nesteds(self):
        related_fields = []
        for field_name, field in self.fields.items():
            if isinstance(field, RelatedNested):
                related_fields.append((field_name, field))
        return OrderedDict(related_fields)

    def _serialize(self, obj, many=False, *args, **kwargs):
        if many and isinstance(obj, models.Manager):
            obj = obj.get_queryset()
            if self.opts.order_by:
                obj = obj.order_by(*self.opts.order_by)
        return super()._serialize(obj, many=many)

    @property
    def validated_data(self):
        if not hasattr(self, '_validated_data'):
            raise AssertionError(
                'You must call `.validate()` before accessing the schema `validated_data` attribute.'
            )
        return self._validated_data

    @property
    def load_data(self):
        if not hasattr(self, '_load_data'):
            raise AssertionError(
                'You must call `.load()` before accessing the schema `load_data` attribute.'
            )
        return self._load_data

    def _do_load(self, data, **kwargs):
        self._load_data = super()._do_load(data, **kwargs)
        self._validated_data = data
        return self._load_data

    def update(self, instance, validated_data=None, partial=True, **kwargs):
        """Update model instance fields with a `validated_data`"""
        if not isinstance(instance, self.model_class):
            raise TypeError(f'`instance` parameter must be instance of `{self.model_class.__name__}` class.')

        kwargs['partial'] = partial
        return self.save(
            validated_data=validated_data,
            instance=instance,
            **kwargs
        )

    def _save_m2m(self, instance, load_data=None):
        """
            Save the many-to-many fields and generic relations.
        """

        def _save_from_data(instance, load_data):
            model_opts = instance._meta
            for f in chain(model_opts.many_to_many, model_opts.private_fields):
                if f.name in self.related_fields:
                    rel = self.related_fields[f.name]
                    if rel.many:
                        m2m_items = load_data[f.name]
                        f.save_form_data(instance, m2m_items)

        if not self.many:
            _save_from_data(instance, load_data)
        else:
            for data in load_data:
                _save_from_data(instance, data)

    def save(self, validated_data=None, many=None, instance=None, **kwargs):
        many = self.many if many is None else bool(many)
        if not validated_data:
            validated_data = self.validated_data
        load_data = self.load(validated_data, many=many, **kwargs)

        if not many:
            for related_name, related_field in self.related_nesteds.items():
                if related_name in load_data:
                    load_data[related_name] = related_field.schema.save()
            instance = construct_instance(
                schema=self,
                data=load_data,
                instance=instance
            )
            instance.save()
            self._save_m2m(instance, load_data)
        else:
            instance = [self.save(vd, many=False, **kwargs) for vd in validated_data]

        return instance

    def handle_error(self, error: ValidationError, data: typing.Any, *, many: bool, **kwargs):
        error_message_overrides = self.opts.error_message_overrides or {}
        handled_errors = {}
        for key, override_message in error_message_overrides.items():
            if isinstance(key, str):
                handled_errors[key] = override_message
                continue

            if issubclass(key, Field) and isinstance(error.messages, dict):
                # override error message for same type of schema field
                for field_name, message in error.messages.items():
                    schema_field = self.fields.get(field_name)
                    if type(schema_field) is key:
                        handled_errors[field_name] = override_message

        if handled_errors:
            error_messages = error.messages
            error_messages.update(handled_errors)
            raise ValidationError(
                error_messages,
                error.field_name,
                error.data,
                error.valid_data,
                **error.kwargs
            )


class ModelSchema(BaseModelSchema):
    pass


def modelschema_factory(model, schema=ModelSchema, fields=None, exclude=None, **kwargs):
    """
        Return a ModelSchema containing schema fields for the given model.
    """
    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude
    attrs.update(kwargs)
    bases = (ModelSchema.Meta,) if hasattr(ModelSchema, 'Meta') else ()
    Meta = type('Meta', bases, attrs)

    # Give this new Schema class a reasonable name.
    class_name = model.__name__ + 'Schema'

    # Class attributes for the new form class.
    schema_class_attrs = {
        'Meta': Meta,
    }

    if getattr(Meta, 'fields', None) is None and getattr(Meta, 'exclude', None) is None:
        raise ImproperlyConfigured(
            'Defining `nested_fields` options for a schema or calling modelschema_factory without defining "fields" or '
            f'"exclude" explicitly is prohibited. Model: {model}'
        )

    return type(schema)(class_name, (schema,), schema_class_attrs)
