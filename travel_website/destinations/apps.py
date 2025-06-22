from django.apps import AppConfig

class DestinationsConfig(AppConfig):
    name = 'destinations'

    def ready(self):
        from . import signals  # noqa
