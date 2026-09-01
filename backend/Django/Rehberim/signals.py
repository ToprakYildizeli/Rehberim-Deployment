"""Rehberim domain sinyalleri.

Bağımlılık yönü korunur: Rehberim, accounts'u dinler — accounts Rehberim'i bilmez.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Counselor

from .models import Achievement


@receiver(post_save, sender=Counselor, dispatch_uid='seed_counselor_achievements')
def seed_counselor_achievements(sender, instance: Counselor, created: bool, **kwargs) -> None:
    """Yeni rehbere varsayılan başarım setini kopyalar (C3).

    Yalnızca **oluşturulurken** çalışır: rehber varsayılanlardan birini sildiyse
    sonraki bir kayıt güncellemesi onu geri getirmemeli. Başarımlar rehbere ait
    olduğu için bu kopya sonradan serbestçe düzenlenebilir.
    """
    if created:
        Achievement.seed_defaults(instance)
