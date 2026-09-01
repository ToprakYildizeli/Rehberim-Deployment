from django.apps import AppConfig


class RehberimConfig(AppConfig):
    name = 'Rehberim'

    def ready(self) -> None:
        from . import signals  # noqa: F401  (sinyalleri kaydeder)
