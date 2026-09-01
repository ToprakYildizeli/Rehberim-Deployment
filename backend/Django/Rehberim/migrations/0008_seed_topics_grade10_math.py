from django.db import migrations


# 10. Sınıf Matematik konuları (örnek/başlangıç kataloğu).
# Diğer ders/sınıf konuları admin'den veya sonraki data migration'larla eklenebilir.
GRADE_10_MATH = [
    "Permütasyon",
    "Kombinasyon",
    "Binom Açılımı",
    "Basit Olayların Olasılığı",
    "Fonksiyon Kavramı ve Gösterimi",
    "Fonksiyonların Grafikleri",
    "Bileşke ve Ters Fonksiyon",
    "Polinomlar",
    "Polinomlarda Çarpanlara Ayrılma",
    "İkinci Dereceden Denklemler",
    "Karmaşık Sayılar",
    "Çokgenler ve Özel Dörtgenler (Yamuk, Paralelkenar, Eşkenar Dörtgen, Dikdörtgen, Kare, Deltoid)",
]


def seed(apps, schema_editor):
    Subject = apps.get_model('Rehberim', 'Subject')
    Topic = apps.get_model('Rehberim', 'Topic')
    subject = Subject.objects.filter(name="Matematik", category="okul").first()
    if subject is None:
        return  # Ders seed'i yoksa sessiz geç
    for order, name in enumerate(GRADE_10_MATH):
        Topic.objects.get_or_create(
            subject=subject, grade="10", name=name, defaults={'order': order},
        )


def unseed(apps, schema_editor):
    Subject = apps.get_model('Rehberim', 'Subject')
    Topic = apps.get_model('Rehberim', 'Topic')
    subject = Subject.objects.filter(name="Matematik", category="okul").first()
    if subject is not None:
        Topic.objects.filter(subject=subject, grade="10", name__in=GRADE_10_MATH).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Rehberim', '0007_topic_topicprogress'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
