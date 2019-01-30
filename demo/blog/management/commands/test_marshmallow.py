from django.core.management.base import BaseCommand

from blog.models import Post
from blog.schemas import PostSchema

class Command(BaseCommand):

	def handle(self, *args, **kwargs):
		post = Post(title='hey hey', is_published=False)
		post.save()

		post_schema = PostSchema()
		print(post_schema.dump(post))
