from django_marshmallow import schemas

from blog.models import Post

class PostSchema(schemas.ModelSchema):

    class Meta:
        fields = ('title', 'is_published')
        model = Post
