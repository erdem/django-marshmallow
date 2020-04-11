from rest_framework import serializers

from blog.models import Category, Tag, Post


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'created_at')
        model = Category


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'created_at')
        model = Tag


class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        fields = ('title', 'category', 'tags', 'is_published', 'created_at')
        model = Post
