# destinations/serializers.py
from rest_framework import serializers
from .models import Destination, Spot, SpotImage, Offer

class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Offer
        fields = '__all__'

class SpotImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SpotImage
        fields = ['id', 'image', 'caption', 'order']

class SpotSerializer(serializers.ModelSerializer):
    images  = SpotImageSerializer(many=True, read_only=True)
    offers  = OfferSerializer(many=True, read_only=True)
    class Meta:
        model  = Spot
        fields = '__all__'

class DestinationSerializer(serializers.ModelSerializer):
    spots = SpotSerializer(many=True, read_only=True)
    class Meta:
        model  = Destination
        fields = ['id', 'name', 'slug', 'overview', 'spots']
