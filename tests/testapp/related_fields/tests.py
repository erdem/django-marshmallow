from typing import Any

from django.test import TestCase
from django_marshmallow.schemas import ModelSchema
from .models import DjangoTestModel


class Serialize(ModelSchema):

    class Meta:
        model = DjangoTestModel
        fields = ("id", "name", "create_date")

class TestTestCase(TestCase):

    def test_print(self):
        instance = DjangoTestModel(
            name="first run"
        )
        instance.save()
        serialize = Serialize()
        cc = serialize.dump(instance)
        import ipdb;ipdb.set_trace()

