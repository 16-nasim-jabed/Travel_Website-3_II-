# destinations/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import SpotImage
from .tasks import generate_thumbnails, clear_destination_cache

@receiver(pre_save, sender=SpotImage)
def post_image_upload(sender, instance, **kwargs):
    # After image saved we’ll kick off thumbnail task in model's save method
    if instance.pk is None:
        # new image
        pass

# Cache invalidation task would be scheduled in services after spot update.
