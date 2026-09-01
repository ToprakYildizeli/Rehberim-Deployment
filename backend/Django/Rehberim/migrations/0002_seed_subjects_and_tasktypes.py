from django.db import migrations


TYT_SUBJECTS = [
    "Türkçe", "Tarih", "Coğrafya", "Felsefe", "Din Kültürü ve Ahlak Bilgisi",
    "Matematik", "Geometri", "Fizik", "Kimya", "Biyoloji",
]

AYT_SUBJECTS = [
    "Türk Dili ve Edebiyatı", "Tarih-1", "Coğrafya-1", "Tarih-2", "Coğrafya-2",
    "Felsefe", "Din Kültürü ve Ahlak Bilgisi", "Matematik", "Geometri",
    "Fizik", "Kimya", "Biyoloji",
]

# 9-11. sınıf öğrencilerinin gördüğü okul dersleri
SCHOOL_SUBJECTS = [
    "Türk Dili ve Edebiyatı", "Matematik", "Geometri", "Fizik", "Kimya",
    "Biyoloji", "Tarih", "Coğrafya", "Felsefe", "Din Kültürü ve Ahlak Bilgisi",
    "İngilizce",
]

TASK_TYPES = ["Test", "Deneme", "Konu Çalışması", "Video İzleme"]


def seed(apps, schema_editor):
    Subject = apps.get_model('Rehberim', 'Subject')
    TaskType = apps.get_model('Rehberim', 'TaskType')

    for order, name in enumerate(TYT_SUBJECTS):
        Subject.objects.get_or_create(name=name, category='tyt', defaults={'order': order})
    for order, name in enumerate(AYT_SUBJECTS):
        Subject.objects.get_or_create(name=name, category='ayt', defaults={'order': order})
    for order, name in enumerate(SCHOOL_SUBJECTS):
        Subject.objects.get_or_create(name=name, category='okul', defaults={'order': order})

    for order, name in enumerate(TASK_TYPES):
        TaskType.objects.get_or_create(name=name, defaults={'order': order})


def unseed(apps, schema_editor):
    Subject = apps.get_model('Rehberim', 'Subject')
    TaskType = apps.get_model('Rehberim', 'TaskType')
    Subject.objects.all().delete()
    TaskType.objects.filter(name__in=TASK_TYPES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Rehberim', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
