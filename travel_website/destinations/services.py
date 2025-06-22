# destinations/services.py

from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth import get_user_model

from .models import Offer, OfferImage, Spot, SpotImage

# destinations/services.py
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth import get_user_model
from .models import Offer, OfferImage

User = get_user_model()

from django.core.exceptions import ValidationError


def save_spot(request, destination, instance=None, clear_old_images=False):
    """
    Create Spot + its images. If instance is provided, update it.
    """
    spot_kwargs = {
        'destination': destination,
        'name':       request.POST.get('name', '').strip(),
        'overview':   request.POST.get('overview', '').strip(),
        'address':    request.POST.get('address', '').strip(),
        'latitude':   request.POST.get('latitude') or None,
        'longitude':  request.POST.get('longitude') or None,
    }
    if request.user.is_authenticated:
        spot_kwargs['created_by'] = request.user
        spot_kwargs['modified_by'] = request.user

    if instance:
        # If instance is provided, update the spot
        for key, value in spot_kwargs.items():
            setattr(instance, key, value)
        spot = instance
        spot.save()
    else:
        spot = Spot.objects.create(**spot_kwargs)

    # Optionally replace images if needed
    if clear_old_images:
        spot.images.all().delete()

    files = request.FILES.getlist('images')
    for img in files[:10]:
        SpotImage.objects.create(spot=spot, image=img, order=spot.images.count())

    return spot


def save_offers(request, destination, clear_old=False):
    rows = list(zip(
        request.POST.getlist('offer_type'),
        request.POST.getlist('offer_description'),
        request.POST.getlist('offer_price'),
        request.POST.getlist('offer_from'),
        request.POST.getlist('offer_to'),
        request.POST.getlist('offer_contact'),
    ))

    auth = request.user if request.user.is_authenticated else None

    for idx, (tp, desc, price, av_from, av_to, wa) in enumerate(rows):
        if not tp:
            continue
        offer = Offer.objects.create(
            destination      = destination,
            type             = tp,
            description      = desc,
            price            = price or 0,
            available_from   = av_from or None,
            available_to     = av_to or None,
            contact_whatsapp = wa,
            created_by       = auth,
            modified_by      = auth,
        )

        # Check if files are being passed correctly
        print(f"Uploading images for offer {offer.id}")
        files = request.FILES.getlist(f'offer_images_{idx}')
        print(f"Number of files uploaded: {len(files)}")

        # If files exist, save them
        for img in files[:10]:
            print(f"Saving image for offer {offer.id}: {img.name}")
            OfferImage.objects.create(
                offer = offer,
                image = img,
                order = offer.images.count()
            )
