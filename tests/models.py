import decimal
import tempfile
from types import SimpleNamespace

import pytest
import uuid as uuid
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.db import models


class CustomField(models.CharField):
    """
    A custom model field simply for testing purposes.
    """
    pass


class TestAbstractModel(models.Model):
    class Meta:
        app_label = 'tests'
        abstract = True


class SimpleTestModel(TestAbstractModel):
    name = models.CharField(max_length=255)
    text = models.TextField(blank=True)
    published_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DataFieldsModel(TestAbstractModel):
    """
    A model class for testing data fields (non-related fields).
    """
    auto_field = models.AutoField(primary_key=True)
    big_integer_field = models.BigIntegerField()
    boolean_field = models.BooleanField(default=False)
    char_field = models.CharField(max_length=255)
    date_field = models.DateField()
    datetime_field = models.DateTimeField()
    decimal_field = models.DecimalField(max_digits=3, decimal_places=1)
    email_field = models.EmailField(max_length=255)
    float_field = models.FloatField()
    integer_field = models.IntegerField()
    null_boolean_field = models.NullBooleanField()
    positive_integer_field = models.PositiveIntegerField()
    positive_small_integer_field = models.PositiveSmallIntegerField()
    slug_field = models.SlugField()
    small_integer_field = models.SmallIntegerField()
    text_field = models.TextField()
    file_field = models.FileField()
    time_field = models.TimeField()
    url_field = models.URLField(max_length=255)
    custom_field = CustomField(max_length=255)
    file_path_field = models.FilePathField(path=tempfile.gettempdir())

    @property
    def property_method(self):
        return 'property_method'

    def method(self):
        return 'method'


COLOR_CHOICES = (
    ('red', 'Red'),
    ('blue', 'Blue'),
    ('green', 'Green')
)

DECIMAL_CHOICES = (
    ('low', decimal.Decimal('0.1')),
    ('medium', decimal.Decimal('0.5')),
    ('high', decimal.Decimal('0.9'))
)


class FieldOptionsModel(TestAbstractModel):
    value_limit_field = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    length_limit_field = models.CharField(validators=[MinLengthValidator(3)], max_length=12)
    blank_field = models.CharField(blank=True, max_length=10)
    null_field = models.IntegerField(null=True)
    default_field = models.IntegerField(default=0)
    descriptive_field = models.IntegerField(help_text='Some help text', verbose_name='A label')
    choices_field = models.CharField(max_length=100, choices=COLOR_CHOICES)
    text_choices_field = models.TextField(choices=COLOR_CHOICES)


class ChoicesModel(TestAbstractModel):
    choices_field_with_nonstandard_args = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        choices=DECIMAL_CHOICES,
        verbose_name='A label'
    )


class UniqueChoiceModel(TestAbstractModel):
    CHOICES = (
        ('choice1', 'choice 1'),
        ('choice2', 'choice 1'),
    )

    name = models.CharField(max_length=254, unique=True, choices=CHOICES)


class ManyToManyTarget(TestAbstractModel):
    name = models.CharField(max_length=100)


class ManyToManySource(TestAbstractModel):
    name = models.CharField(max_length=100)
    targets = models.ManyToManyField(ManyToManyTarget, related_name='sources')


class ForeignKeyTarget(TestAbstractModel):
    name = models.CharField(max_length=100)


class SimpleRelationsModel(TestAbstractModel):
    many_to_many_field = models.ManyToManyField(ManyToManyTarget)
    foreign_key_field = models.ForeignKey(
        ForeignKeyTarget,
        on_delete=models.CASCADE
    )


class UUIDForeignKeyTarget(TestAbstractModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)


class ForeignKeySource(TestAbstractModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(
        ForeignKeyTarget,
        related_name='sources',
        help_text='Target',
        verbose_name='Target',
        on_delete=models.CASCADE
    )


class ForeignKeySourceWithLimitedChoices(TestAbstractModel):
    target = models.ForeignKey(
        ForeignKeyTarget,
        help_text='Target',
        verbose_name='Target',
        limit_choices_to={"name__startswith": "limited-"},
        on_delete=models.CASCADE
    )


class ForeignKeySourceWithQLimitedChoices(TestAbstractModel):
    target = models.ForeignKey(
        ForeignKeyTarget,
        help_text='Target',
        verbose_name='Target',
        limit_choices_to=models.Q(name__startswith="limited-"),
        on_delete=models.CASCADE
    )


# Nullable ForeignKey
class NullableForeignKeySource(TestAbstractModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(
        ForeignKeyTarget,
        null=True,
        blank=True,
        related_name='nullable_sources',
        verbose_name='Optional target object',
        on_delete=models.CASCADE
    )


class NullableUUIDForeignKeySource(TestAbstractModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(
        ForeignKeyTarget,
        null=True,
        blank=True,
        related_name='nullable_uuid_sources',
        verbose_name='Optional target object',
        on_delete=models.CASCADE
    )


class NestedForeignKeySource(TestAbstractModel):
    """
    Used for testing FK chain. A -> B -> C.
    """
    name = models.CharField(max_length=100)
    target = models.ForeignKey(
        NullableForeignKeySource,
        null=True,
        blank=True,
        related_name='nested_sources',
        verbose_name='Intermediate target object',
        on_delete=models.CASCADE
    )


# OneToOne
class OneToOneTarget(TestAbstractModel):
    name = models.CharField(max_length=100)


class NullableOneToOneSource(TestAbstractModel):
    name = models.CharField(max_length=100)
    target = models.OneToOneField(
        OneToOneTarget,
        null=True,
        blank=True,
        related_name='nullable_source',
        on_delete=models.CASCADE
    )


class OneToOnePKSource(TestAbstractModel):
    """ Test model where the primary key is a OneToOneField with another model. """
    name = models.CharField(max_length=100)
    target = models.OneToOneField(
        OneToOneTarget,
        primary_key=True,
        related_name='required_source',
        on_delete=models.CASCADE
    )