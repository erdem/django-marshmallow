from django_marshmallow import schemas

class CitySchema(schemas.ModelSchema):

    class Meta:
        fields = ('country', 'name')
        model = City
