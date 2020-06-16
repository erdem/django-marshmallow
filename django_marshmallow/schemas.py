import copy
from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.functional import cached_property
from marshmallow.schema import SchemaMeta, SchemaOpts

from marshmallow import Schema

from django_marshmallow.converter import ModelFieldConverter
from django_marshmallow.fields import RelatedField, RelatedNested
from django_marshmallow.utils import get_field_info


ALL_FIELDS = '__all__'


class ModelSchemaOpts(SchemaOpts):

    def __init__(self, meta, ordered: bool = False):
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

        self.order_by = getattr(meta, 'order_by', ())
        if not isinstance(self.order_by, (list, tuple)):
            raise ValueError("`order_by` schema option must be a list or tuple.")

        self.model_converter = getattr(meta, 'model_converter', ModelFieldConverter)
        self.depth = getattr(meta, 'depth', None)
        self.ordered = getattr(meta, 'ordered', True)
        self.include_pk = getattr(meta, 'include_pk', True)
        self.expand_related_pk_fields = getattr(meta, 'expand_related_pk_fields', True)
        self.show_select_options = getattr(meta, 'show_select_options', False)
        self.use_file_url = getattr(meta, 'use_file_url', True)
        self.domain_for_files_url = getattr(meta, 'domain_for_files_url', None)


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
        include_pk = opts.include_pk

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

        if not isinstance(include_pk, bool):
            raise ValueError(
                '`include_pk` option must be a boolean.'
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
        if self.opts.include_pk:
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
                'You must call `.load()` or `.validate()` before accessing `.validated_data`.'
            )
        return self._validated_data

    def _do_load(self, data, **kwargs):
        self._validated_data = super()._do_load(data, **kwargs)
        return self._validated_data

    def save(self, validated_data=None, commit=True):
        data = validated_data or self.validated_data
        ModelClass = self.opts.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in data):
                many_to_many[field_name] = data.pop(field_name)

        try:
            if self.many:
                instance = []
                for d in data:
                    o = ModelClass(**d)
                    o.save()
                    instance.append(o)
            else:
                instance = ModelClass._default_manager.create(**data)
        except TypeError:
            msg = (
                'Got a `TypeError` when calling `%s.%s.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.%s.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception' %
                (
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    self.__class__.__name__,
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance


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
