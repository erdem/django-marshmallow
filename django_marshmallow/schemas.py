import copy

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from marshmallow.schema import SchemaMeta, SchemaOpts

from marshmallow import Schema

from django_marshmallow.converter import ModelFieldConverter


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
        if many:
            obj = obj.get_queryset()
        return super()._serialize(obj, many=many)


class ModelSchema(BaseModelSchema):
    pass
