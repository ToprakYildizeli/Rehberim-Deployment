from django.db import migrations


# En çok kullanılan yayınevleri (kaynak: Yayinevleri.pdf). Kitap eklerken dropdown.
PUBLISHERS = [
    "3D Yayınları", "Açılım Yayınları", "Açı Yayınları", "Acil Yayınları",
    "Aktif Öğrenme Yayınları", "Apotemi Yayınları", "Ayna Yayınları",
    "Aydın Yayınları", "Benim Hocam Yayınları", "Bilgi Sarmal Yayınları",
    "Biyoloji Parkı / Biyotik Yayınları", "Bıyıklı Matematik Yayınları",
    "Çap Yayınları", "Delta Kültür Yayınevi", "Derece Yayınları",
    "Doğru Cevap Yayınları", "Doktrin Yayınları", "Editör Yayınevi",
    "Endam Yayınları", "Esen Yayınları", "Evrensel İletişim Yayınları",
    "Extreme Yayınları", "Formül Yayınları", "Gür Yayınları",
    "Hız ve Renk Yayınları", "İdeal Kondisyon Yayınları", "İki A Yayınları",
    "İşler Yayın Grubu", "Kafa Dengi Yayınları", "Karakök Yayınları",
    "Karekök Yayınları", "Köşebilgi Yayınları", "Krallar Karması",
    "Kültür Yayınları", "Kuram Yayınları", "Limit Yayınları", "Marka Yayınları",
    "Mert Hoca Yayınları", "Metin Yayınları", "Mikroorijinal / Orijinal Akademi",
    "More & More (Kurmay Yayınları)", "Mozaik Yayınları", "Nitelik Yayınları",
    "Okyanus Yayınları", "Orbital Yayınları", "Orijinal Yayınları",
    "Örnek Akademi", "Palme Yayınevi", "Paraf Yayınları", "Pelikan Yayınevi",
    "Prf Yayınları (Z Takımı)", "Puan Yayınları", "Radikal Yayınları",
    "Rehber Matematik Yayınları", "Şenol Hoca Yayınları", "Sınav Yayınları",
    "Sonuç Yayınları", "Tasarı Yayınları", "Toprak Yayıncılık", "Taslak Yayınları",
    "Taktiklerle Türkçe Yayınları", "Tasarı Akademi Yayınları",
    "Teas Press / Cinius Yayınları", "ÜçDörtBeş (345) Yayınları", "Uğur Yayınları",
    "VİP Yayınları", "Yargı Yayınevi", "Yayın Denizi PRO",
]


def seed(apps, schema_editor):
    Publisher = apps.get_model('Rehberim', 'Publisher')
    for order, name in enumerate(PUBLISHERS):
        Publisher.objects.get_or_create(name=name, defaults={'order': order})


def unseed(apps, schema_editor):
    Publisher = apps.get_model('Rehberim', 'Publisher')
    Publisher.objects.filter(name__in=PUBLISHERS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Rehberim', '0010_seed_topics_full'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
