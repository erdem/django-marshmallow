import copy
from collections import OrderedDict
from itertools import chain

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import IPAddressField
from django.utils.functional import cached_property
from marshmallow.schema import SchemaMeta, SchemaOpts

from marshmallow import Schema, fields

from django_marshmallow.utils import get_field_info

ALL_FIELDS = '__all__'


class ModelSchemaOpts(SchemaOpts):

    def __init__(self, meta, ordered: bool = False):
        fields = getattr(meta, 'fields', None)

        # Bypass Marshmallow Option class validation for "__all__" fields. #FixMe
        if fields == ALL_FIELDS:
            meta.fields = ()
        super(ModelSchemaOpts, self).__init__(meta, ordered)
        if self.fields == ():
            self.fields = None
        self.model = getattr(meta, 'model', None)
        self.level = getattr(meta, 'level', None)
        self.exclude = getattr(meta, 'exclude', ())


class FileField(fields.Inferred):
    pass


class ImageField(fields.Inferred):
    pass


class SlugField(fields.Inferred):
    pass


class IPAddress(fields.Inferred):
    pass


class FilePath(fields.Inferred):
    pass


SCHEMA_FIELD_MAPPING = {
    models.AutoField: fields.Integer,
    models.BigIntegerField: fields.Integer,
    models.BooleanField: fields.Boolean,
    models.CharField: fields.String,
    models.CommaSeparatedIntegerField: fields.String,
    models.DateField: fields.Date,
    models.DateTimeField: fields.DateTime,
    models.DecimalField: fields.Decimal,
    models.EmailField: fields.Email,
    models.Field: fields.Inferred,
    models.FileField: FileField,
    models.FloatField: fields.Float,
    models.ImageField: ImageField,
    models.IntegerField: fields.Integer,
    models.NullBooleanField: fields.Boolean,
    models.PositiveIntegerField: fields.Integer,
    models.PositiveSmallIntegerField: fields.Integer,
    models.SlugField: SlugField,
    models.SmallIntegerField: fields.Integer,
    models.TextField: fields.String,
    models.TimeField: fields.Time,
    models.URLField: fields.URL,
    models.GenericIPAddressField: IPAddress,
    models.FilePathField: FilePath,
    models.DurationField: fields.TimeDelta,
}


def fields_for_model(model, fields, exclude, **kwargs):
    model_field_info = get_field_info(model)
    field_list = []
    ignored = []
    for field_name, field in model_field_info.all_fields.items():
        if fields is not None and field_name not in fields:
            continue
        if exclude and field_name in exclude:
            continue
        model_schema_field = SCHEMA_FIELD_MAPPING.get(field.__class__)

        if model_schema_field:
            field_list.append((field_name, model_schema_field(**kwargs)))
        else:
            ignored.append((field_name, field))
    field_dict = OrderedDict(field_list)
    return field_dict


class ModelSchemaMetaclass(SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelSchemaMetaclass, mcs).__new__(mcs, name, bases, attrs)
        opts = new_class._meta = new_class.OPTIONS_CLASS(meta=getattr(new_class, 'Meta', None))

        if opts.model:
            # If a model is defined, extract form fields from it.
            if opts.fields is None and opts.exclude is None:
                raise ImproperlyConfigured(
                    "Creating a ModelForm without either the 'fields' attribute "
                    "or the 'exclude' attribute is prohibited; form %s "
                    "needs updating." % name
                )

            if opts.fields == ALL_FIELDS:
                # Sentinel for fields_for_model to indicate "get the list of
                # fields from the model"
                opts.fields = None

            fields = fields_for_model(opts.model, opts.fields, opts.exclude)

            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = {k for k, v in fields.items() if not v}
            missing_fields = none_model_fields.difference(new_class._declared_fields)
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise TypeError(message)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(new_class._declared_fields)
        else:
            fields = new_class._declared_fields

        new_class._declared_fields = fields

        return new_class


class BaseModelSchema(Schema, metaclass=ModelSchemaMetaclass):
    OPTIONS_CLASS = ModelSchemaOpts

    def get_fields(self):
        return copy.deepcopy(self._declared_fields)

    @cached_property
    def fields(self):
        return self.get_fields()


class ModelSchema(BaseModelSchema):
    pass
