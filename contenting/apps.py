from django.apps import AppConfig


class ContentingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contenting'

    def ready(self):
        # noinspection PyUnresolvedReferences
        import contenting.signals
