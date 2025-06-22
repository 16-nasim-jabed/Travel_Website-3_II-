# destinations/api.py
from rest_framework import routers, viewsets, permissions
from .models import Destination, Spot
from .serializers import DestinationSerializer, SpotSerializer

class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Destination.objects.prefetch_related('spots')
    serializer_class = DestinationSerializer
    permission_classes = [permissions.AllowAny]

class SpotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Spot.objects.with_related()
    serializer_class = SpotSerializer
    permission_classes = [permissions.AllowAny]

router = routers.DefaultRouter()
router.register('destinations', DestinationViewSet)
router.register('spots', SpotViewSet)
