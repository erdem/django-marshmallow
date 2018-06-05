from marshmallow import fields


class DMField(fields.Field):

    def __init__(self, attribute=None, **kwargs):
        super(DMField, self).__init__(**kwargs)
        self.attribute = attribute.split('.') if attribute else []

    def get_value(self, attr, obj, accessor=None, default=missing_):
        return super().get_value(attr, obj, accessor, default)

