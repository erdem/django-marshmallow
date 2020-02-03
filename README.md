### Notice: The stable version is not avaiable. Currently, it's prototype and still developing. Feel free to contribute ideas and PRs.   

This is a package that making serialization for django model objects and major python data types. It is a wrapper for [marsmallow package](https://marshmallow.readthedocs.io). The main aim is serialize the django model class objects.

Examples:

`models.py`

```python
    from django.db import models

    class Country(models.Model):
        name = models.CharField()
        created_at = models.DateTimeField(auto_now_add=True)

    class City(models.Model):
        country = models.ForeignKey(Country)
        name = models.CharField()
        created_at = models.DateTimeField(auto_now_add=True)
```

`schemas.py`

```python
    from django_marshmallow import schemas

    class CitySchema(schemas.ModelSchema):

        class Meta:
            fields = ('country', 'name')
            model = City

    country = Country(name='United Kingdom')
    city = City(country=country, name='London')
    city.save()

    city_schema = CitySchema()
    city_schema.dump(city)
    # {
    #     'id': 1
    #     'country_id': 1,
    #     'name': 'London'
    # }
```

```python
    from django_marshmallow import schemas, fields

    class CountrySchema(schemas.ModelSchema):
        class Meta:
            fields = ('id', 'name')
            model = City

    class CitySchema(schemas.ModelSchema):
        country = fields.Nested(CountrySchema)
        created_at = fields.Date()

        class Meta:
            fields = ('id', 'country', 'name', 'created_at')
            model = City

    country = Country(name='United Kingdom')
    city = City(country=country, name='London')
    city.save()

    city_schema = CitySchema()
    city_schema.dump(city)
    # {
    #     'id': 1
    #     'country': {
    #         'id': 1
    #         'name': 'United Kingdom'
    #     },
    #     'name': 'London',
    #     'created_at': 2018-09-09:17:23
    # }
```


