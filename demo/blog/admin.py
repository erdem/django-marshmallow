import json

from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from marshmallow import Schema, fields
from rest_framework import serializers

from blog.models import Post, Category, Tag
from django_marshmallow.schemas import ModelSchema


class PostSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Post
        depth = 2


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'category', 'tags', 'post')


class PostOrginalSchema(Schema):
    title = fields.Str()
    created_at = fields.DateTime()


class CategorySchema(ModelSchema):

    class Meta:
        model = Category
        fields = '__all__'


class PostModelSchema(ModelSchema):

    class Meta:
        model = Post
        fields = '__all__'
        ordered = True
        level = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', )
    list_filter = ('category', 'tags')

    def rest_serializer_response(self, post):
        serializer = PostSerializer(instance=post)
        return mark_safe(f'<pre>{json.dumps(serializer.data, indent=4)}</pre>')

    def original_schema_response(self, post):
        schema = PostOrginalSchema()
        data = schema.dump(post)
        return mark_safe(f'<pre>{json.dumps(data, indent=4)}</pre>')

    def load_model_schema(self, post):
        if Post.objects.filter(title='first schema post').exists():
            return 'done'
        else:
            Category.objects.filter(name='new category').delete()
            Tag.objects.filter(name='new tag 1').delete()
            Tag.objects.filter(name='new tag 2').delete()
        schema = PostModelSchema()
        data = {
            'title': 'first schema post',
            'is_published': True,
            'category': {
                'name': 'new category'
            },
            'tags': [
                {
                    'name': 'new tag 1',
                },
                {
                    'name': 'new tag 2'
                }
            ]
        }
        data = schema.load(data)
        instance = schema.save()
        print(f'instance id is {instance.id}')
        return mark_safe(f'<pre>{json.dumps(schema.dump(instance), indent=4)}</pre>')

    def model_schema_response(self, post):
        schema = PostModelSchema()
        data = schema.dump(Post.objects.filter(title='first schema post').first())
        return mark_safe(f'<pre>{json.dumps(data, indent=4)}</pre>')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super().change_view(request, object_id, form_url, extra_context)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    list_filter = ('created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    list_filter = ('created_at',)


admin.register(Tag)
admin.register(Category)
