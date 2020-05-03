# import decimal
# import tempfile
# from types import SimpleNamespace
#
# import pytest
#
# from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.db import models


class CustomField(models.Field):
    """
    A custom model field simply for testing purposes.
    """
    pass



class TestBaseModel(models.Model):
    class Meta:
        app_label = 'tests'
        abstract = True


class SimpleRegularModel(TestBaseModel):
    char_field = models.CharField(max_length=255)

#
# class RegularFieldsModel(TestBaseModel):
#     """
#     A model class for testing regular flat fields.
#     """
#     auto_field = models.AutoField(primary_key=True)
#     big_integer_field = models.BigIntegerField()
#     boolean_field = models.BooleanField(default=False)
#     char_field = models.CharField(max_length=100)
#     comma_separated_integer_field = models.CommaSeparatedIntegerField(max_length=100)
#     date_field = models.DateField()
#     datetime_field = models.DateTimeField()
#     decimal_field = models.DecimalField(max_digits=3, decimal_places=1)
#     email_field = models.EmailField(max_length=100)
#     float_field = models.FloatField()
#     integer_field = models.IntegerField()
#     null_boolean_field = models.NullBooleanField()
#     positive_integer_field = models.PositiveIntegerField()
#     positive_small_integer_field = models.PositiveSmallIntegerField()
#     slug_field = models.SlugField(max_length=100)
#     small_integer_field = models.SmallIntegerField()
#     text_field = models.TextField(max_length=100)
#     file_field = models.FileField(max_length=100)
#     time_field = models.TimeField()
#     url_field = models.URLField(max_length=100)
#     custom_field = CustomField()
#     file_path_field = models.FilePathField(path=tempfile.gettempdir())
#
#     def method(self):
#         return 'method'
#
# COLOR_CHOICES = (
#     ('red', 'Red'),
#     ('blue', 'Blue'),
#     ('green', 'Green')
# )
#
# DECIMAL_CHOICES = (
#     ('low', decimal.Decimal('0.1')),
#     ('medium', decimal.Decimal('0.5')),
#     ('high', decimal.Decimal('0.9'))
# )
#
# class FieldOptionsModel(models.Model):
#     value_limit_field = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
#     length_limit_field = models.CharField(validators=[MinLengthValidator(3)], max_length=12)
#     blank_field = models.CharField(blank=True, max_length=10)
#     null_field = models.IntegerField(null=True)
#     default_field = models.IntegerField(default=0)
#     descriptive_field = models.IntegerField(help_text='Some help text', verbose_name='A label')
#     choices_field = models.CharField(max_length=100, choices=COLOR_CHOICES)
#     text_choices_field = models.TextField(choices=COLOR_CHOICES)
#
# class ChoicesModel(models.Model):
#     choices_field_with_nonstandard_args = models.DecimalField(
#         max_digits=3,
#         decimal_places=1,
#         choices=DECIMAL_CHOICES,
#         verbose_name='A label'
#     )
#
# class UniqueChoiceModel(models.Model):
#     CHOICES = (
#         ('choice1', 'choice 1'),
#         ('choice2', 'choice 1'),
#     )
#
#     name = models.CharField(max_length=254, unique=True, choices=CHOICES)
#
