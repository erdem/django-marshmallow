from django_marshmallow.schemas import ModelSchema


def test_file_field_model_save(db, db_models, uploaded_file_obj, uploaded_image_file_obj):
    class TestSchema(ModelSchema):

        class Meta:
            model = db_models.FileFieldModel
            fields = ('name', 'file_field', 'image_field')

    assert db_models.FileFieldModel.objects.count() == 0

    schema = TestSchema()
    save_data = {
        'name': 'Created instance',
        'file_field': uploaded_file_obj,
        'image_field': uploaded_image_file_obj
    }
    errors = schema.validate(save_data)
    instance = schema.save()
    assert len(errors) == 0
    assert db_models.FileFieldModel.objects.count() == 1
    assert db_models.FileFieldModel.objects.first().file_field.url == instance.file_field.url
    assert db_models.FileFieldModel.objects.first().image_field.url == instance.image_field.url
