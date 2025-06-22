# destinations/admin.py
from django.contrib import admin
from .models import Destination, Spot, SpotImage, Offer

# Inline for SpotImage under Spot
class SpotImageInline(admin.TabularInline):
    model = SpotImage
    extra = 1
    readonly_fields = ('order',)

# Inline for Offer under Destination
class OfferInline(admin.TabularInline):
    model = Offer
    fk_name = 'destination'       # ← tell the inline which FK to use
    extra = 1
    fields = (
        'type',
        'description',
        'price',
        'available_from',
        'available_to',
        'contact_whatsapp',
    )

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'featured')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [OfferInline]     # now offers appear on the Destination page

@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'created_at', 'featured')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SpotImageInline]  # images appear on the Spot page
