from csv import DictReader
from django.core.management.base import BaseCommand, CommandError
from destinations.services import create_spot
from destinations.models import Destination
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    """Bulk import spots from CSV."""
    help = "Import spots file.csv destination_slug"

    def add_arguments(self, parser):
        parser.add_argument('csv_path')
        parser.add_argument('destination_slug')

    def handle(self, *args, **opts):
        dest = Destination.objects.get(slug=opts['destination_slug'])
        with open(opts['csv_path'], newline='', encoding='utf8') as f:
            for row in DictReader(f):
                data = {
                    'destination': dest,
                    'name':   row['name'],
                    'overview': row['overview'],
                    'latitude': row['lat'] or None,
                    'longitude': row['lon'] or None,
                }
                create_spot(data, files={}, user=get_user_model().objects.first())
                self.stdout.write(self.style.SUCCESS(f"Imported {row['name']}"))
