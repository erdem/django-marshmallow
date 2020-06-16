import typing
from collections import OrderedDict
from urllib.parse import urljoin

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import marshmallow as ma
from marshmallow import ValidationError, validate


class DJMFieldMixin:
    GENERIC_VALIDATORS = {
        'allow_blank': validate.Length(min=1, error='Field cannot be blank')
    }

    def __init__(self, **kwargs):
        self.model_field = kwargs.pop('model_field', None)
        super().__init__(**kwargs)


class FileField(DJMFieldMixin, ma.fields.Field):

    default_error_messages = {
        'required': 'No file was submitted.',
        'invalid': 'The submitted data was not a file. Check the encoding type on the form.',
        'no_name': 'No filename could be determined.',
        'empty': 'The submitted file is empty.',
        'max_length': 'Ensure this filename has at most {max_length} characters (it has {length}).',
    }

    def __init__(self, allow_empty_file=False, max_length=None, **kwargs):
        self.allow_empty_file =allow_empty_file
        self.max_length = max_length
        if 'use_url' in kwargs:
            self.use_url = kwargs.pop('use_url')
        if 'custom_domain' in kwargs:
            self.custom_domain = kwargs.pop('custom_domain')
        super().__init__(**kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            file_name = value.name
            file_size = value.size
        except AttributeError:
            self.make_error('invalid')

        if not file_name:
            self.make_error('no_name')
        if not self.allow_empty_file and not file_size:
            self.fail('empty')
        if self.max_length and len(file_name) > self.max_length:
            self.fail('max_length', max_length=self.max_length, length=len(file_name))

        return value

    def _serialize(self, value, attr, obj, **kwargs):
        if not value:
            return None

        use_url = getattr(self, 'use_url', self.root.opts.use_file_url)
        custom_domain = getattr(self, 'custom_domain', self.root.opts.domain_for_files_url)
        if use_url:
            try:
                url = value.url
            except AttributeError:
                return None
            if custom_domain:
                return urljoin(custom_domain, url)

            request = self.metadata.get('request')
            if request:
                return request.build_absolute_uri(url)

            return url
        return value.name


class ImageField(FileField):

    def _deserialize(self, value, attr, data, **kwargs):
        image_file = super()._deserialize(value, attr, data, **kwargs)
        field_kwargs = self.metadata.get('field_kwargs', {})
        django_form_field = self.model_field.formfield(**field_kwargs)
        django_form_field.error_messages = self.error_messages
        return django_form_field.clean(image_file)


class String(DJMFieldMixin, ma.fields.String):
    def __init__(self, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)
        super().__init__(**kwargs)
        if not self.allow_blank:
            self.validators.append(self.GENERIC_VALIDATORS.get('allow_blank'))


class ChoiceField(String):

    def __init__(self, choices, **kwargs):
        if not isinstance(choices, (list, tuple)):
            raise ValueError(f'{self.name} `choices` must be a list or tuple.')

        self.choices = choices
        super().__init__(**kwargs)
        if self.choices:
            choices_dict = OrderedDict(self.choices)
            choices_validator = validate.OneOf(choices=choices_dict.keys(), labels=choices_dict.values())
            self.validators.append(choices_validator)
            self.select_options = choices_validator.options()

    def _serialize(self, value, attr, obj, **kwargs) -> typing.Optional[str]:
        serialized_data = super()._serialize(value, attr, obj, **kwargs)
        if self.choices and self.root.opts.show_select_options:
            return {
                'value': serialized_data,
                'options': list(self.select_options)
            }
        return serialized_data


### Related fields
class RelatedPKField(ma.fields.Field):

    default_error_messages = {
        'related_object_does_not_exists': '`{field_name}` related field entity does not exists for "{value}" on {related_model}',
        'invalid_value': 'Related primary key value cannot be None'
    }

    def __init__(
            self,
            related_pk_value_field,
            model_field,
            related_model,
            to_field,
            many=False,
            **kwargs
    ):
        super().__init__(**kwargs)
        if many:
            self.related_pk_value_field = ma.fields.List(related_pk_value_field)
            self.missing = list()
        else:
            self.related_pk_value_field = related_pk_value_field
            self.missing = None
        self.model_field = model_field
        self.related_model = related_model
        self.to_field = to_field
        self.many = many

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        related_field_value = getattr(obj, attr, None)
        if self.many and isinstance(related_field_value, models.Manager):
            value = list(related_field_value.values_list('pk', flat=True))
        if self.many and isinstance(related_field_value, list):
            value = [v.pk for v in related_field_value if isinstance(v, self.related_model)]
        if self.to_field:
            value = getattr(related_field_value, self.to_field)
        return self.related_pk_value_field._serialize(value, attr, obj)

    def _validate(self, value):
        if self.many and not isinstance(value, (list, tuple)):
            raise ValidationError('ManytoMany fields values must be `list` or `tuple`')
        return super()._validate(value)

    def _deserialize(self, value, attr=None, data=None, **kwargs):
        if value is None:
            raise self.make_error('invalid_value')
        value = self.related_pk_value_field.deserialize(value, attr, data)

        if self.many and isinstance(value, (list, tuple)):
            invalid_pks = []
            data = []
            for pk in value:
                try:
                    data.append(self.related_model._default_manager.get(pk=pk))
                except ObjectDoesNotExist:
                    invalid_pks.append(pk)

            if invalid_pks:
                raise self.make_error(
                    'related_object_does_not_exists',
                    field_name=self.model_field.name,
                    value=', '.join('{0}'.format(n) for n in invalid_pks),
                    related_model=self.related_model.__name__
                )
            return data

        if self.to_field:
            try:
                return self.related_model._default_manager.get(pk=value)
            except ObjectDoesNotExist:
                raise self.make_error(
                    'related_object_does_not_exists',
                    field_name=self.model_field.name,
                    value=str(value),
                    related_model=self.related_model.__name__
                )
        raise self.make_error('invalid_value')


class RelatedField(ma.fields.Field):

    default_error_messages = {
        'invalid': '`RelatedField` data must be a {type} type.',
        'empty': '`RelatedField` data must be include a valid primary key value for {model_name} model.',
        'too_many_pk': 'Received too many primary key values for single related field.',
        'invalid_keys': 'Received invalid data key(`{invalid_key}`) for `{field_name}` field. The related data key must be `{field_name}` or `pk`',
    }

    def __init__(self, related_pk_field=RelatedPKField, target_field=None, relation_info=None, many=False, **kwargs):
        super().__init__(**kwargs)
        self.related_model = getattr(relation_info, 'related_model', None)
        self.to_field = relation_info.to_field
        self.target_field = target_field
        self.many = many
        self.collection_type = list if many else dict
        self.related_pk_field = related_pk_field
        if many:
            self.missing = list()
        else:
            self.missing = None
        if not self.related_model:
            raise ma.exceptions.MarshmallowError(
                'RelatedNested needs to use with a inherited class of '
                '"ModelSchema" or can use with a Marshmallow "Schema" class implementation along with'
                ' `related_model` parameter.'
            )

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if self.many:
            return [{self.target_field: m} for m in self.related_pk_field.serialize(attr, obj)]
        return {
            self.target_field: self.related_pk_field.serialize(attr, obj)
        }

    def _deserialize(self, value, attr, data, **kwargs):
        if not self.many and not isinstance(value, dict):
            raise self.make_error('invalid', type=dict.__name__)
        if not self.many and len(value) > 1:
            raise self.make_error('too_many_pk')

        if self.many and not isinstance(value, list):
            raise self.make_error('invalid', type=list.__name__)

        if len(value) == 0:
            raise self.make_error('empty', model_name=self.related_model.__name__)

        result = self.collection_type()
        errors = self.collection_type()

        if not self.many:
            data_key = self.target_field if self.target_field in value else 'pk' if 'pk' in value else None
            if data_key is None:
                raise self.make_error(
                    'invalid_keys',
                    field_name=self.target_field,
                    invalid_key=list(value.keys())[0],
                )
            related_pk_value = value.get(data_key)
            try:
                deser_val = self.related_pk_field.deserialize(related_pk_value, **kwargs)
            except ValidationError as error:
                errors[data_key] = error.messages
            else:
                result = deser_val
        else:
            related_pk_values = []
            for item in value:
                data_key = self.target_field if self.target_field in item else 'pk' if 'pk' in item else None
                if data_key is None:
                    raise self.make_error(
                        'invalid_keys',
                        field_name=self.target_field,
                        invalid_key=list(item.keys())[0],
                    )
                related_pk_values.append(item.get(data_key))

            try:
                deser_val = self.related_pk_field.deserialize(related_pk_values, **kwargs)
            except ValidationError as error:
                errors.append({data_key: error.messages})
            else:
                result = deser_val

        if errors:
            raise ValidationError(errors, valid_data=result)

        return result


class RelatedNested(ma.fields.Nested):

    def __init__(self, nested, **kwargs):
        super().__init__(nested, **kwargs)
        self.related_model = kwargs.get('related_model', getattr(nested.opts, 'model', None))
        if not self.related_model:
            raise ma.exceptions.MarshmallowError(
                'RelatedNested needs to use with a inherited class of '
                '"ModelSchema" or can use with a Marshmallow "Schema" class implementation along with'
                ' `related_model` parameter.'
            )

    def deserialize(self, value, attr=None, data=None, **kwargs):
        data = super().deserialize(value, attr, data, **kwargs)
        if data:
            if self.many:
                instance = [self.related_model(**d) for d in data]
            else:
                instance = self.related_model(**data)
            return instance
        return data


class Mapping(DJMFieldMixin, ma.fields.Mapping):
    pass


class Dict(DJMFieldMixin, ma.fields.Dict):
    pass


class List(DJMFieldMixin, ma.fields.List):
    pass


class Tuple(DJMFieldMixin, ma.fields.Tuple):
    pass


class UUID(DJMFieldMixin, ma.fields.UUID):
    pass


class Number(DJMFieldMixin, ma.fields.Number):
    pass


class Integer(DJMFieldMixin, ma.fields.Integer):
    pass


class Decimal(DJMFieldMixin, ma.fields.Decimal):
    pass


class Boolean(DJMFieldMixin, ma.fields.Boolean):
    pass


class Float(DJMFieldMixin, ma.fields.Float):
    pass


class DateTime(DJMFieldMixin, ma.fields.DateTime):
    pass


class NaiveDateTime(DJMFieldMixin, ma.fields.NaiveDateTime):
    pass


class AwareDateTime(DJMFieldMixin, ma.fields.AwareDateTime):
    pass


class Time(DJMFieldMixin, ma.fields.Time):
    pass


class Date(DJMFieldMixin, ma.fields.Date):
    pass


class TimeDelta(DJMFieldMixin, ma.fields.TimeDelta):
    pass


class Url(DJMFieldMixin, ma.fields.Url):
    pass


class Email(DJMFieldMixin, ma.fields.Email):
    pass


class Method(DJMFieldMixin, ma.fields.Method):
    pass


class Function(DJMFieldMixin, ma.fields.Function):
    pass


class Constant(DJMFieldMixin, ma.fields.Constant):
    pass


class Pluck(DJMFieldMixin, ma.fields.Pluck):
    pass


class InferredField(DJMFieldMixin, ma.fields.Inferred):

    def __init__(self, **kwargs):
        super().__init__()


class BinaryField(DJMFieldMixin, ma.fields.Field):
    pass


class CommaSeparatedIntegerField(InferredField):
    pass


class FilePathField(InferredField):
    pass


class GenericIPAddressField(InferredField):
    pass


class IPAddressField(InferredField):
    pass


class SlugField(InferredField):
    pass


# Aliases
URL = Url
Str = String
Bool = Boolean
Int = Integer
