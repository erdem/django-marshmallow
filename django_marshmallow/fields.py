

class Field(object):

    def __init__(self, attribute=None, **kwargs):
        super(Field, self).__init__(**kwargs)


class RawField(Field):
    pass


class NestedField(Field):
    pass


class DictField(Field):
    pass


class ListField(Field):
    pass


class StringField(Field):
    pass


class UUIDField(Field):
    pass


class NumberField(Field):
    pass


class IntegerField(Field):
    pass


class DecimalField(Field):
    pass


class BooleanField(Field):
    pass


class FormattedStringField(Field):
    pass


class FloatField(Field):
    pass


class DateTimeField(Field):
    pass


class LocalDateTimeField(Field):
    pass


class TimeField(Field):
    pass


class DateField(Field):
    pass


class TimeDeltaField(Field):
    pass


class URLField(Field):
    pass


class EmailField(Field):
    pass


class MethodField(Field):
    pass


class FunctionField(Field):
    pass


class ConstantField(Field):
    pass

