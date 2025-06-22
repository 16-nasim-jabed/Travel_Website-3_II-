# destinations/tasks.py
from celery import shared_task
from django.core.cache import cache
from .models import SpotImage

@shared_task
def generate_thumbnails(image_id):
    """Pretend to resize images asynchronously."""
    img = SpotImage.objects.get(pk=image_id)
    # … image processing here …

@shared_task
def clear_destination_cache(destination_id):
    cache_key = f'dest-{destination_id}'
    cache.delete(cache_key)
