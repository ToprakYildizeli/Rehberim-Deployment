from django.db import migrations


# Ders başına sınav soru sayısı (= alınabilecek maksimum net).
# TYT toplam 120, AYT toplam 160 (ÖSYM YKS güncel dağılımı).
TYT_COUNTS = {
    "Türkçe": 40,
    "Tarih": 5,
    "Coğrafya": 5,
    "Felsefe": 5,
    "Din Kültürü ve Ahlak Bilgisi": 5,
    "Matematik": 30,
    "Geometri": 10,
    "Fizik": 7,
    "Kimya": 7,
    "Biyoloji": 6,
}

AYT_COUNTS = {
    "Türk Dili ve Edebiyatı": 24,
    "Tarih-1": 10,
    "Coğrafya-1": 6,
    "Tarih-2": 11,
    "Coğrafya-2": 11,
    "Felsefe": 12,
    "Din Kültürü ve Ahlak Bilgisi": 6,
    "Matematik": 30,
    "Geometri": 10,
    "Fizik": 14,
    "Kimya": 13,
    "Biyoloji": 13,
}


def seed_counts(apps, schema_editor):
    Subject = apps.get_model("Rehberim", "Subject")
    for name, count in TYT_COUNTS.items():
        Subject.objects.filter(category="tyt", name=name).update(question_count=count)
    for name, count in AYT_COUNTS.items():
        Subject.objects.filter(category="ayt", name=name).update(question_count=count)


def unseed_counts(apps, schema_editor):
    Subject = apps.get_model("Rehberim", "Subject")
    Subject.objects.exclude(category="okul").update(question_count=0)


class Migration(migrations.Migration):

    dependencies = [
        ("Rehberim", "0016_subject_question_count"),
    ]

    operations = [
        migrations.RunPython(seed_counts, unseed_counts),
    ]
