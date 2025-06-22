import os
import uuid
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

USER = get_user_model()

def _slugify_uniquely(model, base):
    """Generate a unique slug for the model."""
    slug = base
    n = 1
    while model.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug

def spot_image_path(instance, filename):
    """Generate a unique file path for spot images."""
    ext = filename.split('.')[-1]
    return os.path.join(
        'spots', str(instance.spot.id), f"{uuid.uuid4().hex}.{ext}"
    )

def offer_image_path(instance, filename):
    """Generate a unique file path for offer images."""
    ext = filename.split('.')[-1]
    return os.path.join(
        'offers',
        str(instance.offer.id),
        f"{uuid.uuid4().hex}.{ext}"
    )

# TimeStamped model to track creation and modification times
class TimeStamped(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by  = models.ForeignKey(
        USER, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='%(class)s_created'
    )
    modified_by = models.ForeignKey(
        USER, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='%(class)s_modified'
    )
    class Meta:
        abstract = True

# Destination model
class Destination(TimeStamped):
    name     = models.CharField(max_length=255)
    slug     = models.SlugField(unique=True, blank=True)
    overview = models.TextField(blank=True)
    featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _slugify_uniquely(Destination, slugify(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# Spot model
class SpotManager(models.Manager):
    def with_related(self):
        return (self.get_queryset()
                    .select_related('destination')
                    .prefetch_related('images'))

class Spot(TimeStamped):
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name='spots'
    )
    name     = models.CharField(max_length=255)
    slug     = models.SlugField(blank=True)
    overview = models.TextField(blank=True)
    address  = models.TextField(blank=True, default='')
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude= models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    featured = models.BooleanField(default=False)

    objects = SpotManager()

    class Meta:
        ordering        = ['name']
        unique_together = [('destination', 'slug')]
        constraints = [
            models.UniqueConstraint(
                fields=['destination', 'name'],
                name='unique_spot_per_destination'
            )
        ]

    def clean(self):
        if not self.name:
            raise ValidationError("Name required")
        if bool(self.latitude) ^ bool(self.longitude):
            raise ValidationError("Must supply both latitude and longitude")

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            self.slug = _slugify_uniquely(Spot, f"{self.destination.slug}-{base}")
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.destination.name}: {self.name}"

# SpotImage model to store images for spots
class SpotImage(TimeStamped):
    spot    = models.ForeignKey(
        Spot, on_delete=models.CASCADE, related_name='images'
    )
    image   = models.ImageField(upload_to=spot_image_path)
    caption = models.CharField(max_length=255, blank=True)
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def clean(self):
        if not self.pk and self.spot.images.count() >= 10:
            raise ValidationError("Max 10 images per Spot.")

# Offer model to store offers for destinations
class Offer(TimeStamped):
    HOTEL = 'hotel'
    PLAN = 'plan'
    BOAT = 'boat'
    TRAIN = 'train'
    TYPES = [
        (HOTEL, "Hotel"),
        (PLAN,  "Plan"),
        (BOAT,  "Boat"),
        (TRAIN, "Train"),
    ]

    destination      = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name='offers'
    )
    type             = models.CharField(max_length=10, choices=TYPES)
    description      = models.TextField(blank=True)
    price            = models.DecimalField(max_digits=10, decimal_places=2)
    available_from   = models.DateField()
    available_to     = models.DateField()
    contact_whatsapp = models.CharField(max_length=50)

    class Meta:
        ordering = ['available_from']
        constraints = [
            models.CheckConstraint(
                check=Q(available_from__lte=models.F('available_to')),
                name='offer_valid_date_range'
            )
        ]

    def clean(self):
        if self.available_from > self.available_to:
            raise ValidationError("From date must be before To date.")

    def __str__(self):
        return f'{self.get_type_display()} @ {self.destination.name}'

# OfferImage model to store images for offers
class OfferImage(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='offers/%Y/%m/%d/')  # Check this line carefully
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
