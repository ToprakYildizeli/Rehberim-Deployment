# Haftalık Program — Backend Tasarım Planı

> Durum: TASLAK · Tarih: 2026-07-13
> Kapsam: Öğretmen (rehber) ve öğrencinin DERS + METOD + SÜRE detaylı görev
> girebildiği, rehberin haftalık program oluşturduğu, öğrencinin bu programı
> görüp doğrudan düzenleyebildiği backend özelliği.

## 1. Kararlar

| Konu | Karar |
|------|-------|
| METOD | Mevcut `TaskType` yeniden kullanılır (Test, Deneme, Konu Çalışması, Video...) |
| SÜRE | `start_time` (başlangıç saati) + `duration_minutes` (dakika) |
| Program periyodu | Görüşme gününden başlayan **7 günlük** program (`start_date`; sabit haftalık takvim değil) |
| Öğrenci düzenlemesi | Doğrudan (onay akışı yok) |
| Oluşturan | Hem rehber hem öğrenci görev (ProgramItem) ekleyebilir; `created_by` ile izlenir |

## 2. Yeni Modeller (`Rehberim/models.py`)

### WeeklyProgram
Bir öğrenciye ait, görüşme gününden başlayan 7 günlük program.

| Alan | Tip | Not |
|------|-----|-----|
| `student` | FK → accounts.Student | `related_name='programs'` |
| `counselor` | FK → accounts.Counselor (null) | Programı oluşturan hoca |
| `start_date` | DateField | Görüşme günü; program `start_date`..`start_date+6` |
| `note` | CharField(blank) | Opsiyonel haftalık not |
| `created_at` / `updated_at` | auto | |

- `end_date` (property) = `start_date + 6 gün`
- `Meta`: `ordering=['-start_date']`, `unique_together=('student','start_date')`
- "Güncel program" = bugünü kapsayan (`start_date <= today <= end_date`) ya da en yeni.

### ProgramItem  (= DERS + METOD + SÜRE "task")
Programdaki tek bir çalışma bloğu.

| Alan | Tip | Not |
|------|-----|-----|
| `program` | FK → WeeklyProgram | `related_name='items'` |
| `subject` | FK → Subject (null) | **DERS** |
| `task_type` | FK → TaskType (null) | **METOD** |
| `date` | DateField | Hafta içindeki gün (`start_date`..`+6` aralığında doğrulanır) |
| `start_time` | TimeField | Başlangıç saati |
| `duration_minutes` | PositiveIntegerField | **SÜRE** |
| `title` | CharField(blank) | Opsiyonel serbest başlık |
| `description` | TextField(blank) | Opsiyonel |
| `is_completed` | Bool | Öğrenci tamamlandı işaretler |
| `created_by` | FK → accounts.User (null) | Hoca mı öğrenci mi ekledi |
| `order` | PositiveSmallInt | Aynı gün içi sıralama |

- `end_time` (property) = `start_time + duration_minutes`
- `Meta`: `ordering=['date','start_time','order']`
- Doğrulama: `date` program aralığında olmalı; `duration_minutes > 0`.

> Not: Mevcut `Task` modeli (ödev + due_date) ayrı bir özelliktir; dokunulmaz.
> Haftalık program için ayrı `ProgramItem` kullanmak semantiği temiz tutar.

## 3. Serializers (`Rehberim/serializers.py` — yeni)

- `SubjectSerializer`, `TaskTypeSerializer` — frontend'de DERS/METOD dropdown'ları için.
- `ProgramItemSerializer` — subject/task_type (id + isim), date, start_time,
  duration_minutes, end_time (read-only), is_completed, created_by (read-only).
- `WeeklyProgramSerializer` — student, counselor, start_date, end_date (read-only),
  items (nested, güne göre gruplanabilir).

## 4. Endpoint'ler (`Rehberim/api_urls.py` — yeni, `/api/` altına include)

Mevcut manuel `path()` + generic APIView desenine sadık kalınır (router yok).

**Referans veri (dropdown doldurma):**
| Method | URL | Açıklama |
|--------|-----|----------|
| GET | `/api/subjects/` | Öğrencinin sınıfına göre uygun dersler (`available_subjects`) |
| GET | `/api/task-types/` | METOD listesi |

**Programlar:**
| Method | URL | Kim | Açıklama |
|--------|-----|-----|----------|
| GET | `/api/programs/` | öğrenci: kendi · rehber: öğrencileri | Liste |
| POST | `/api/programs/` | rehber | Öğrenciye program aç (`student`, `start_date`) |
| GET | `/api/programs/{id}/` | ilgili öğrenci + rehber | Detay + items |
| PATCH | `/api/programs/{id}/` | rehber (+öğrenci note) | Düzenle |
| DELETE | `/api/programs/{id}/` | rehber | Sil |
| GET | `/api/programs/current/` | öğrenci | Bugünü kapsayan güncel program |

**Görevler (ProgramItem):**
| Method | URL | Kim | Açıklama |
|--------|-----|-----|----------|
| POST | `/api/programs/{id}/items/` | rehber + öğrenci | Görev ekle (DERS/METOD/SÜRE/gün/saat) |
| PATCH | `/api/items/{id}/` | rehber + öğrenci | Düzenle |
| DELETE | `/api/items/{id}/` | rehber + öğrenci | Sil |
| PATCH | `/api/items/{id}/` (`is_completed`) | öğrenci | Tamamlandı işaretle |

## 5. İzinler (`Rehberim/permissions.py` — yeni obje-bazlı)

- Rehber, yalnızca **kendi** öğrencilerinin (`student.counselor == user.counselor_profile`)
  programını oluşturur/düzenler/siler.
- Öğrenci, yalnızca **kendi** programını görür ve item'larını doğrudan düzenler.
- Mevcut `IsCounselor` / `IsStudent` sınıfları rol kapısı olarak kullanılır; üstüne
  `IsProgramOwner` obje-bazlı kontrol eklenir.
- Veli: bu sürümde salt-okunur dışında kapsam dışı (yol haritası).

## 6. Diğer

- `Rehberim/admin.py`: WeeklyProgram (inline ProgramItem) + kayıtlar.
- Migration: `makemigrations Rehberim` + `migrate`.
- Testler: model doğrulamaları (date aralığı, süre) + endpoint izinleri
  (rehber başka öğrenciye yazamaz, öğrenci kendi item'ını düzenler) — `pytest`/DRF
  `APITestCase`. Kanıt olarak çalıştırılıp çıktı eklenir.
- `docs/auth-contract.md` gibi kısa bir `docs/program-contract.md` ile frontend'e
  endpoint sözleşmesi verilir (dropdown'lar + program/item şekilleri).

## 7. Uygulama Sırası (adımlar)

1. Modeller (`WeeklyProgram`, `ProgramItem`) + migration.
2. Admin kaydı (hızlı manuel doğrulama için).
3. Serializers.
4. İzinler (obje-bazlı).
5. Endpoint'ler (referans veri → programlar → item'lar).
6. `api_urls` include + smoke test (curl/DRF).
7. Testler + `program-contract.md`.
8. Commit'ler (conventional): `feat(program): models`, `feat(program): api`, `test`, `docs`.
