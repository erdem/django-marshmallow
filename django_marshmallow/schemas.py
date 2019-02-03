from django.db import models
from django_marshmallow import SchemaOpts as MarshmallowSchemaOpts, fields
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
        klass = self.__class__
        output = {}
        
        for key, field in self._declaredFields.items():
            output[key] = field.to_python(getattr(instance, field.attribute))

        return output


class ModelSchemaMeta(type):
    """Metaclass for ModelSchema."""

    def __init__(cls, name, bases, dct):
        super(ModelSchemaMeta, cls).__init__(name, bases, dct)
        _declaredFields = {}
        for key, value in dct.items():
            if (isinstance(value, fields.DMField)):
                _declaredFields[key] = value
        cls._declaredFields = _declaredFields


class ModelSchema(with_metaclass(ModelSchemaMeta, Base)):
    OPTIONS_CLASS = ModelSchemaOpts
