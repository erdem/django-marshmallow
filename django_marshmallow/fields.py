

class DMField(object):

    def __init__(self, attribute=None, **kwargs):
        super(DMField, self).__init__(**kwargs)


class RawField(DMField):
    pass


class NestedField(DMField):
    pass


class DictField(DMField):
    pass


class ListField(DMField):
    pass


class StringField(DMField):
    pass


class UUIDField(DMField):
    pass


class NumberField(DMField):
    pass


class IntegerField(DMField):
    pass


class DecimalField(DMField):
    pass


class BooleanField(DMField):
    pass


class FormattedStringField(DMField):
    pass


class FloatField(DMField):
    pass


class DateTimeField(DMField):
    pass


class LocalDateTimeField(DMField):
    pass


class TimeField(DMField):
    pass


class DateField(DMField):
    pass


class TimeDeltaField(DMField):
    pass


class URLField(DMField):
    pass


class EmailField(DMField):
    pass


class MethodField(DMField):
    pass


class FunctionField(DMField):
    pass


class ConstantField(DMField):
    pass

