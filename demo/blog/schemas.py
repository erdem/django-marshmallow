from django_marshmallow import schemas, fields

from blog.models import Post

class PostSchema(schemas.ModelSchema):

    title = fields.RawField('title')
    is_published = fields.BooleanField('is_published')
    a_list = fields.ListField('title')
    uppercased = fields.RawField('title', formatter=lambda x: x.upper())

    class Meta:
        model = Post
