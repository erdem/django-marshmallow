from __future__ import unicode_literals

import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _


class DjangoMarshmallowTestModel(models.Model):
    """
    Base model for tests
    """

    class Meta:
        abstract = True

#
# class BasicModel(DjangoMarshmallowTestModel):
#     text = models.CharField(max_length=100)
#
#
# # ForeignKey
# class ForeignKeyTarget(DjangoMarshmallowTestModel):
#     text = models.CharField(
#         max_length=100,
#         verbose_name=_("Text comes here"),
#         help_text=_("Text description.")
#     )
#
#
# class UUIDForeignKeyTarget(DjangoMarshmallowTestModel):
#     uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     name = models.CharField(max_length=100)
#
#
# class ForeignKeySource(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#     target = models.ForeignKey(ForeignKeyTarget, related_name='sources',
#                                help_text='Target', verbose_name='Target',
#                                on_delete=models.CASCADE)
#
#
# class NullableForeignKeySource(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#     target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
#                                related_name='nullable_sources',
#                                verbose_name='Optional target object',
#                                on_delete=models.CASCADE)
#
#
# class NullableUUIDForeignKeySource(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#     target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
#                                related_name='nullable_sources',
#                                verbose_name='Optional target object',
#                                on_delete=models.CASCADE)
#
#
# class NestedForeignKeySource(DjangoMarshmallowTestModel):
#     """
#     Used for testing FK chain. A -> B -> C.
#     """
#     name = models.CharField(max_length=100)
#     target = models.ForeignKey(NullableForeignKeySource, null=True, blank=True,
#                                related_name='nested_sources',
#                                verbose_name='Intermediate target object',
#                                on_delete=models.CASCADE)
#
#
# # OneToOne
# class OneToOneTarget(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#
#
# class NullableOneToOneSource(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#     target = models.OneToOneField(
#         OneToOneTarget, null=True, blank=True,
#         related_name='nullable_source', on_delete=models.CASCADE)
#
#
# class OneToOnePKSource(DjangoMarshmallowTestModel):
#     """ Test model where the primary key is a OneToOneField with another model. """
#     name = models.CharField(max_length=100)
#     target = models.OneToOneField(
#         OneToOneTarget, primary_key=True,
#         related_name='required_source',
#         on_delete=models.CASCADE)
#
#
# # ManyToMany
# class ManyToManyTarget(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#
#
# class ManyToManySource(DjangoMarshmallowTestModel):
#     name = models.CharField(max_length=100)
#     targets = models.ManyToManyField(ManyToManyTarget, related_name='sources')


class DjangoTestModel(models.Model):
    name = models.CharField(max_length=255, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
