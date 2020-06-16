from django.core.exceptions import ValidationError
from django.db import models


def validate_category_name(value):
    if not '+' in value:
        raise ValidationError(
            _('%(value)s add "+" plus'),
            params={'value': value},
        )


class Category(models.Model):
    name = models.CharField(max_length=255, validators=[validate_category_name])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or ''


class Tag(models.Model):
    name = models.CharField(max_length=255)
    related_tags = models.ManyToManyField(
        'blog.Tag',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or ''


class Post(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(null=True, upload_to='uploads/')
    file = models.FileField(null=True, upload_to='uploads2/')
    title = models.CharField(max_length=255)
    post = models.TextField(blank=True, null=True)
    is_published = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or ''
