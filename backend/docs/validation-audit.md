# Backend Doğrulama & Bütünlük Denetimi

> Tarih: 2026-07-13 · Yöntem: canlı uç-durum probe'ları + otomatik testler.
> Amaç: veri bütünlüğü kurallarının frontend'e değil backend'e bağlı olduğunu
> garanti etmek (backend = tek doğru kaynak, son savunma hattı).

## Düzeltilenler

| # | Sorun | Durum |
|---|-------|-------|
| 1 | Aynı e-posta ile birden fazla hesap açılabiliyordu | ✅ Düzeltildi — `BaseRegisterSerializer.validate_email` (harf duyarsız), üç kayıt tipini de kapsar. Test var. |
| 2 | Öğrenci kaydında sınıf↔alan tutarlılığı yoktu (12. sınıf alansız, ya da 9. sınıf alanlı kayıt olabiliyordu) | ✅ Düzeltildi — `StudentRegisterSerializer.validate` model kuralını API'de zorunlu kılar. Test var. |
| 3 | Aynı saate birden fazla görev eklenebiliyordu (çakışma) | ✅ Düzeltildi — `ProgramItemSerializer.validate` aynı gün zaman aralığı çakışan görevi reddeder (bitişik serbest). Test var. |

## Kontrol edildi, sağlam çıktı

| Senaryo | Sonuç |
|---------|-------|
| Geçersiz `grade` değeri | 400 ✓ |
| Zayıf şifre | 400 ✓ (`validate_password`) |
| Eksik zorunlu alan (first_name vb.) | 400 ✓ |
| Aynı öğrenciye aynı gün 2. program | 400 ✓ (`unique_together`, DRF otomatik doğrular) |
| Olmayan `student` id ile program | 400 ✓ |
| `connect-counselor`'ı rehberin çağırması | 403 ✓ (rol izni) |
| Korumalı uçlar token'sız / geçersiz token | 401 ✓ |
| Program görevi: süre ≤ 0 / gün program aralığı dışında | 400 ✓ |
| Başkasının programına/görevine erişim | 403 ✓ |
| JWT: login/refresh/logout(blacklist) | ✓ (bkz. auth akışı) |

## Bilinçli olarak zorlanmayan (karar/gelecek)

- **Görev dersi ile öğrenci sınıfı uyumu:** `POST items` herhangi bir dersi kabul
  eder (ürün kararı: her ders serbest). Frontend `/api/subjects/` ile filtreli
  liste gösterir ama backend dersi öğrencinin sınıfına kısıtlamaz.
- **E-posta benzersizliği DB seviyesinde değil** (yalnızca serializer). Bu uygulamada
  hesaplar sadece register API'sinden açıldığı için yeterli; DB `unique=True`
  sertleştirmesi ayrı bir migration + yerel veri temizliği ister.
- **Süre üst sınırı / gece yarısını aşan bitiş:** `end_time` sarabilir; kritik değil.

## Testler

`python manage.py test accounts Rehberim` → 20 test, hepsi geçiyor.
Yeni doğrulamalar için regresyon testleri `accounts/tests.py` içinde.

## Güncelleme (2026-08-08)

- **TYT/AYT konu kataloğu seed edildi** (`Rehberim/migrations/0013_seed_topics_tyt_ayt`,
  10 TYT + 12 AYT dersi, 286 konu, `curriculum=eski`/`grade=12`). Referans veridir;
  **yeni doğrulama kuralı eklenmedi**. Migration temiz uygulandı, `manage.py check` ve
  `makemigrations --check` temiz. Uçtan uca doğrulandı: sınav öğrencisi (12/mezun)
  `available_subjects()` → 22 sınav dersi görüyor, `TopicListView` curriculum'u
  otomatik `eski` çözüp konuları döndürüyor.
- **Rutin / tekrarlayan program:** ertelendi (ileride kesin yapılacak). Bkz. `CLAUDE.md`
  "Bilinen Eksikler / Yol Haritası".
