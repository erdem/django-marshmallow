from django.db import models
from django_marshmallow import SchemaOpts as MarshmallowSchemaOpts
from six import with_metaclass


from django_marshmallow import fields


class ModelSchemaOpts(MarshmallowSchemaOpts):

    def __init__(self, meta, *args, **kwargs):
        super(ModelSchemaOpts, self).__init__(meta)
        self.fields = getattr(meta, 'fields', '__all__')
        self.model = getattr(meta, 'model', None)
        self.level = getattr(meta, 'level', None)


MAPPING = {
    models.CharField: fields.StringField,
    models.DateTimeField: fields.DateTimeField
}


class Base(object):
    def dump(self, instance):
        return 'dump'

class ModelSchemaMeta(type):
    """Metaclass for ModelSchema."""

    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        declared_fields = dict_cls()
        opts = klass.opts
        base_fields = super().get_declared_fields(
            klass, cls_fields, inherited_fields, dict_cls
        )
        declared_fields = mcs.get_fields(opts, base_fields, dict_cls)
        declared_fields.update(base_fields)
        return declared_fields

    @classmethod
    def get_fields(mcs, opts, base_fields, dict_cls):
        if opts.model is not None:
            return {
                'id': fields.IntegerField(),
                'name': fields.StringField(),
                'create_date': fields.StringField(),
            }
        return dict_cls()


class ModelSchema(with_metaclass(ModelSchemaMeta, Base)):
    OPTIONS_CLASS = ModelSchemaOpts
