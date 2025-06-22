from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from users.helpers import get_authenticated_user, admin_required
from .models import Destination, Spot, Offer, SpotImage, OfferImage
from .services import save_offers, save_spot
from django.contrib import messages  # To show success or error messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Offer, OfferImage



# ──────────────────────── PUBLIC ──────────────────────────
def public_destination_list(request):
    user = get_authenticated_user(request)
    destinations = Destination.objects.prefetch_related('spots').all()
    return render(request, 'destinations/list.html', {
        'destinations': destinations,
        'user': user,
    })

def public_destination_detail(request, slug):
    """
    GET /destinations/<slug>/
    Shows one region plus its Spots and its Offers (with images).
    """
    user = get_authenticated_user(request)

    # Prefetch both spots and offer→images in one go:
    destination = get_object_or_404(
        Destination.objects
            .prefetch_related('spots')                # spots list
            .prefetch_related('offers__images'),      # each offer.images
        slug=slug
    )

    return render(request, 'destinations/destination_detail.html', {
        'destination': destination,
        'spots': destination.spots.all(),
        'offers': destination.offers.all(),  # images already prefetched
        'user': user,
    })


def public_spot_detail(request, dest_slug, spot_slug):
    user = get_authenticated_user(request)
    spot = get_object_or_404(
        Spot.objects.with_related(),
        destination__slug=dest_slug,
        slug=spot_slug
    )
    return render(request, 'destinations/spot_detail.html', {
        'spot': spot,
        'user': user,
    })


# ───────────── DESTINATION ADMIN (regions) ────────────────
# ───────────── DESTINATION ADMIN (regions) ────────────────
@admin_required
def admin_destination_list(request):
    places = Destination.objects.prefetch_related('offers').all().order_by('-created_at')
    return render(request, 'destinations/admin_list.html', {
        'places': places,
    })

@admin_required
def admin_destination_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        overview = request.POST.get('overview', '').strip()
        if not name:
            return render(request, 'destinations/admin_region_form.html', {
                'error': 'Name is required.',
            })

        dest = Destination.objects.create(
            name=name,
            overview=overview,
        )

        return redirect('dest_admin_list')

    return render(request, 'destinations/admin_region_form.html', {})

# ───────────────── OFFER ADMIN ─────────────────

@admin_required
def admin_offer_add(request):
    if request.method == 'POST':
        destination_slug = request.POST.get('destination')
        destination = get_object_or_404(Destination, slug=destination_slug)
        
        offer_type = request.POST.get('offer_type')
        description = request.POST.get('offer_description')
        price = request.POST.get('offer_price')
        available_from = request.POST.get('offer_from')
        available_to = request.POST.get('offer_to')
        contact_whatsapp = request.POST.get('offer_contact')

        offer = Offer.objects.create(
            destination=destination,
            type=offer_type,
            description=description,
            price=price,
            available_from=available_from,
            available_to=available_to,
            contact_whatsapp=contact_whatsapp
        )

        # Saving images
        offer_images = request.FILES.getlist('offer_images')
        for img in offer_images[:10]:
            OfferImage.objects.create(offer=offer, image=img)

        return redirect('dest_admin_list')

    destinations = Destination.objects.all()
    return render(request, 'destinations/admin_offer_form.html', {
        'destinations': destinations,
        'offer_type_choices': Offer.TYPES
    })

@admin_required
def admin_offer_edit(request, id):
    offer = get_object_or_404(Offer, id=id)

    if request.method == 'POST':
        offer.type = request.POST.get('offer_type')
        offer.description = request.POST.get('offer_description')
        offer.price = request.POST.get('offer_price')
        offer.available_from = request.POST.get('offer_from')
        offer.available_to = request.POST.get('offer_to')
        offer.contact_whatsapp = request.POST.get('offer_contact')
        offer.save()

        # Handle uploaded images
        offer_images = request.FILES.getlist('offer_images')
        for img in offer_images[:10]:
            OfferImage.objects.create(offer=offer, image=img)

        return redirect('dest_admin_list')

    return render(request, 'destinations/admin_offer_edit_form.html', {
        'offer': offer,
        'offer_type_choices': Offer.TYPES
    })


from django.shortcuts import render, get_object_or_404, redirect
from .models import Offer, Destination
from .services import save_offers


@admin_required
def admin_offer_delete(request, id):
    # Fetch the offer by id
    offer = get_object_or_404(Offer, id=id)

    if request.method == 'POST':
        # Delete the offer
        offer.delete()
        messages.success(request, 'Offer successfully deleted!')
        return redirect('dest_admin_list')  # Redirect to the destinations list page

    return render(request, 'destinations/admin_offer_confirm_delete.html', {
        'offer': offer
    })




@admin_required
def admin_destination_edit(request, slug):
    dest = get_object_or_404(Destination, slug=slug)
    if request.method == 'POST':
        dest.name = request.POST.get('name', '').strip()
        dest.overview = request.POST.get('overview', '').strip()
        dest.save()

        # Save offers (optional)
        save_offers(request, dest, clear_old=True)

        return redirect('dest_admin_list')

    return render(request, 'destinations/admin_region_form.html', {
        'destination': dest,
        'offer_type_choices': Offer.TYPES,  # Pass the Offer.TYPES for dropdown
    })


@admin_required
def admin_destination_delete(request, slug):
    dest = get_object_or_404(Destination, slug=slug)
    if request.method == 'POST':
        dest.delete()
        return redirect('dest_admin_list')
    return render(request, 'destinations/admin_region_confirm_delete.html', {
        'destination': dest,
    })


# ──────────────── SPOT ADMIN (per region) ────────────────
@admin_required
def admin_spot_list(request, dest_slug):
    dest = get_object_or_404(Destination, slug=dest_slug)
    spots = dest.spots.all().order_by('-created_at')
    return render(request, 'destinations/admin_spot_list.html', {
        'destination': dest,
        'spots': spots,
    })


# ─── SPOT ADMIN ────────────────────────────────────────────
@admin_required
def admin_spot_add(request, dest_slug):
    dest = get_object_or_404(Destination, slug=dest_slug)
    if request.method == 'POST':
        save_spot(request, destination=dest)
        return redirect('dest_admin_spot_list', dest_slug=dest.slug)

    return render(request, 'destinations/admin_spot_form.html', {
        'destination': dest,
    })


@admin_required
def admin_spot_edit(request, dest_slug, spot_slug):
    dest = get_object_or_404(Destination, slug=dest_slug)
    spot = get_object_or_404(Spot, destination=dest, slug=spot_slug)
    if request.method == 'POST':
        save_spot(request, destination=dest, instance=spot, clear_old_images=True)
        return redirect('dest_admin_spot_list', dest_slug=dest.slug)

    return render(request, 'destinations/admin_spot_form.html', {
        'destination': dest,
        'spot': spot,
    })

@admin_required
def admin_spot_delete(request, dest_slug, spot_slug):
    dest = get_object_or_404(Destination, slug=dest_slug)
    spot = get_object_or_404(Spot, destination=dest, slug=spot_slug)
    if request.method == 'POST':
        spot.delete()
        return redirect('dest_admin_spot_list', dest_slug=dest.slug)
    return render(request, 'destinations/admin_spot_confirm_delete.html', {
        'destination': dest,
        'spot': spot,
    })

