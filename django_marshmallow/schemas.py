import copy
import typing

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.functional import cached_property
from marshmallow.schema import SchemaMeta, SchemaOpts

from marshmallow import Schema, types

from django_marshmallow.converter import ModelFieldConverter
from django_marshmallow.utils import get_field_info

ALL_FIELDS = '__all__'


class ModelSchemaOpts(SchemaOpts):

    def __init__(self, meta, ordered: bool = False):
        fields = getattr(meta, 'fields', None)
        # Bypass Marshmallow Option class validation for "__all__" fields. FixMe
        if fields == ALL_FIELDS:
            meta.fields = ()
        super(ModelSchemaOpts, self).__init__(meta, ordered)
        if self.fields == ():
            self.fields = None
        self.model = getattr(meta, 'model', None)
        self.model_converter = getattr(meta, 'model_converter', ModelFieldConverter)
        self.level = getattr(meta, 'level', 0)

        self.include_fk = getattr(meta, "include_fk", False)
        self.include_relationships = getattr(meta, "include_relationships", True)
        # Default load_instance to True for backwards compatibility
        self.load_instance = getattr(meta, "load_instance", True)


class ModelSchemaMetaclass(SchemaMeta):

    @classmethod
    def validate_schema_class(mcs, klass):
        opts = klass.opts
        if opts.model:
            # If a model is defined, extract form fields from it.
            if opts.fields is None and opts.exclude is None:
                raise ImproperlyConfigured(
                    "Creating a ModelForm without either the 'fields' attribute "
                    "or the 'exclude' attribute is prohibited; form %s "
                    "needs updating." % klass.__class__.__name__
                )
        level = opts.level
        if level is not None:
            assert level >= 0, "'level' may not be negative."
            assert level <= 10, "'level' may not be greater than 10."
        # FixMe add all cases



    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        """Updates declared fields with fields converted from the SQLAlchemy model
        passed as the `model` class Meta option.
        """
        mcs.validate_schema_class(klass)
        opts = klass.opts
        if opts.fields == ALL_FIELDS:
            # Sentinel for fields_for_model to indicate "get the list of
            # fields from the model"
            opts.fields = None
        Converter=opts.model_converter
        converter = Converter(schema_cls=klass)
        declared_fields = super().get_declared_fields(
            klass, cls_fields, inherited_fields, dict_cls
        )
        fields = mcs.get_fields(converter, klass, opts, declared_fields, dict_cls)
        fields.update(declared_fields)
        return fields

    @classmethod
    def get_fields(mcs, converter, klass, opts, base_fields, dict_cls):
        if opts.model is not None:
            return converter.fields_for_model(
                opts.model,
                klass,
                fields=opts.fields,
                exclude=opts.exclude,
                include_fk=opts.include_fk,
                include_relationships=opts.include_relationships,
                base_fields=base_fields,
                dict_cls=dict_cls,
            )
        return dict_cls()


class BaseModelSchema(Schema, metaclass=ModelSchemaMetaclass):
    OPTIONS_CLASS = ModelSchemaOpts

    def get_fields(self):
        return copy.deepcopy(self._declared_fields)

    @cached_property
    def fields(self):
        return self.get_fields()

    def _serialize(self, obj, many=False, *args, **kwargs):
        if many and isinstance(obj, models.Manager):
            obj = obj.get_queryset()
        return super()._serialize(obj, many=many)

    def validate(self, data: typing.Mapping, *, many: bool = None,
                 partial: typing.Union[bool, types.StrSequenceOrSet] = None) -> typing.Dict[str, typing.List[str]]:
        return super().validate(data, many=many, partial=partial)

    def load(self, data, **kwargs):
        validated_data = super().load(data, **kwargs)
        if self.many:
            return [self.save(v) for v in data]
        return self.save(validated_data)

    def save(self, validated_data):
        ModelClass = self.opts.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

            # if not relation_info.to_many and relation_info.to_field and (field_name in validated_data):
            #     relation = validated_data[field_name]
            #     relation.save()
            #     validated_data[field_name] = relation


        try:
            instance = ModelClass._default_manager.create(**validated_data)
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
