"""Mevcut rehberlere varsayılan başarım setini kopyalar (C3).

Yeni rehberler `Rehberim.signals.seed_counselor_achievements` ile tohumlanır;
bu migration ondan önce kaydolmuş rehberleri yakalar.

Liste bilerek **burada kopyalanmıştır**: migration'lar tarihsel bir anı temsil
eder ve canlı modelden okumamalıdır — `Achievement.DEFAULTS` sonradan
değiştirilse ya da kaldırılsa bu migration'ın davranışı değişmemeli.
"""
from django.db import migrations

DEFAULTS = [
    ('exam_net', 'tyt', 60, "TYT 60 Net", "TYT denemesinde 60 net"),
    ('exam_net', 'tyt', 80, "TYT 80 Net", "TYT denemesinde 80 net"),
    ('exam_net', 'tyt', 90, "TYT 90 Net", "TYT denemesinde 90 net"),
    ('exam_net', 'tyt', 100, "TYT 100 Net", "TYT denemesinde 100 net"),
    ('exam_net', 'tyt', 110, "TYT 110 Net", "TYT denemesinde 110 net"),
    ('topic_completion', '', 25, "Konuların %25'i", "Konuların dörtte biri tamamlandı"),
    ('topic_completion', '', 50, "Konuların %50'si", "Konuların yarısı tamamlandı"),
    ('topic_completion', '', 75, "Konuların %75'i", "Konuların dörtte üçü tamamlandı"),
    ('topic_completion', '', 100, "Tüm Konular", "Bütün konular tamamlandı"),
    ('compliance', '', 60, "Program Uyumu %60", "Onaylı haftalarda %60 uyum"),
    ('compliance', '', 80, "Program Uyumu %80", "Onaylı haftalarda %80 uyum"),
    ('compliance', '', 100, "Tam Uyum", "Onaylı haftalarda %100 uyum"),
]


def seed(apps, schema_editor):
    Counselor = apps.get_model('accounts', 'Counselor')
    Achievement = apps.get_model('Rehberim', 'Achievement')
    for counselor in Counselor.objects.all():
        existing = set(
            Achievement.objects.filter(counselor_id=counselor.id)
            .values_list('name', flat=True)
        )
        Achievement.objects.bulk_create([
            Achievement(
                counselor_id=counselor.id, metric=metric, scope=scope,
                threshold=threshold, name=name, description=description, order=i,
            )
            for i, (metric, scope, threshold, name, description) in enumerate(DEFAULTS)
            if name not in existing
        ])


def unseed(apps, schema_editor):
    """Geri alma: yalnızca varsayılan **adlara** sahip satırları siler.
    Rehberin kendi eklediği başarımlar korunur."""
    Achievement = apps.get_model('Rehberim', 'Achievement')
    Achievement.objects.filter(name__in=[row[3] for row in DEFAULTS]).delete()


class Migration(migrations.Migration):
    dependencies = [('Rehberim', '0026_achievement')]
    operations = [migrations.RunPython(seed, unseed)]
