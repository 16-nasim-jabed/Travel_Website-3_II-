# In your 'urls.py'

from django.urls import path
from .views import (
    # Public
    public_destination_list,
    public_destination_detail,
    public_spot_detail,
    # Admin dest
    admin_destination_list,
    admin_destination_add,
    admin_destination_edit,
    admin_destination_delete,
    # Admin spots
    admin_spot_list,
    admin_spot_add,
    admin_spot_edit,
    admin_spot_delete,
    # Admin offer
     admin_offer_add,
    admin_offer_edit,  # Edit offer view
    admin_offer_delete

)

urlpatterns = [
    # Public list first
    path('', public_destination_list, name='dest_public_list'),

    # ---------- Admin routes ----------
    path('admin/', admin_destination_list, name='dest_admin_list'),
    path('admin/add/', admin_destination_add, name='dest_admin_add'),
    path('admin/<slug:slug>/edit/', admin_destination_edit, name='dest_admin_edit'),
    path('admin/<slug:slug>/delete/', admin_destination_delete, name='dest_admin_delete'),

    # Spot admin - nested under destination
    path('admin/<slug:dest_slug>/spots/', admin_spot_list, name='dest_admin_spot_list'),
    path('admin/<slug:dest_slug>/spots/add/', admin_spot_add, name='dest_admin_spot_add'),
    path('admin/<slug:dest_slug>/spots/<slug:spot_slug>/edit/', admin_spot_edit, name='dest_admin_spot_edit'),
    path('admin/<slug:dest_slug>/spots/<slug:spot_slug>/delete/', admin_spot_delete, name='dest_admin_spot_delete'),

    # ---------- Public detail routes ----------
    path('<slug:dest_slug>/<slug:spot_slug>/', public_spot_detail, name='spot_detail'),
    path('<slug:slug>/', public_destination_detail, name='dest_detail'),

    # Admin routes for offers
    # Admin routes for offers
   path('admin/offer/add/', admin_offer_add, name='dest_admin_offer_add'),
    path('admin/offer/edit/<int:id>/', admin_offer_edit, name='dest_admin_offer_edit'),

    path('admin/offer/delete/<int:id>/', admin_offer_delete, name='dest_admin_offer_delete'),
]

