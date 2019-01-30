from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    post = models.TextField(blank=True, null=True)
    create_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField()

    def __str__(self):
    	return self.title
