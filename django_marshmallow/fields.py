from marshmallow import fields


class DMField(fields.Field):

    def __init__(self, attribute=None, **kwargs):
        super(DMField, self).__init__(**kwargs)


class RawField(fields.Raw, DMField):
    pass


class NestedField(fields.Nested, DMField):
    pass


class DictField(fields.Dict, DMField):
    pass


class ListField(fields.List, DMField):
    pass


class StringField(fields.String, DMField):
    pass


class UUIDField(fields.UUID, DMField):
    pass


class NumberField(fields.Number, DMField):
    pass


class IntegerField(fields.Integer, DMField):
    pass


class DecimalField(fields.Decimal, DMField):
    pass


class BooleanField(fields.Boolean, DMField):
    pass


class FormattedStringField(fields.FormattedString, DMField):
    pass


class FloatField(fields.Float, DMField):
    pass


class DateTimeField(fields.DateTime, DMField):
    pass


class LocalDateTimeField(fields.LocalDateTime, DMField):
    pass


class TimeField(fields.Time, DMField):
    pass


class DateField(fields.Date, DMField):
    pass


class TimeDeltaField(fields.TimeDelta, DMField):
    pass


class URLField(fields.URL, DMField):
    pass


class EmailField(fields.Email, DMField):
    pass


class MethodField(fields.Method, DMField):
    pass


class FunctionField(fields.Function, DMField):
    pass


class ConstantField(fields.Constant, DMField):
    pass

