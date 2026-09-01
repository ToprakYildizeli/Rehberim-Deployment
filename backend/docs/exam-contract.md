# Rehberim — Denemeler API Kontratı

> **Sürüm:** v1.2 · **Durum:** TASLAK · **Tarih:** 2026-08-29
>
> **v1.2 (2026-08-29, E3):** **veli** artık çocuğunun denemelerini salt-okunur görüyor — liste ve detay, ders kırılımıyla (`subject_nets`: doğru/yanlış/boş/net). Program verisinin aksine **onay şartı yoktur**: deneme programa bağlı değil. Veli `?student=`
> ile tek çocuğa daraltabilir; hiçbir denemeyi değiştiremez/silemez.
>
> **v1.1 (yol haritası E1):** denemeye `source` alanı eklendi — kişisel mi
> kurumsal mı. Varsayılan `personal`, mevcut kayıtlar da böyle işaretlendi;
> geriye dönük uyumlu.
>
> Öğrencinin girdiği deneme sonuçları ve ders bazlı netler. Auth: tüm uçlar
> `Authorization: Bearer <access>` ister. Ders id'leri `GET /api/subjects/`'ten.

## Roller
- **Öğrenci:** kendi denemelerini ekler / görür / düzenler / siler.
- **Rehber:** kendi öğrencilerinin denemelerini **yalnızca görür** (girmez/düzenlemez).

## Deneme objesi
```json
{
  "id": 1,
  "student": 7,
  "student_name": "Ali Yılmaz",
  "exam_type": "tyt",              // "tyt" | "ayt" | "" (opsiyonel)
  "source": "personal",            // "personal" | "institutional" — varsayılan "personal"
  "name": "TYT Deneme 1",         // opsiyonel serbest ad
  "exam_date": "2026-07-13",
  "total_net": 43.5,              // netlerin otomatik toplamı (salt-okunur)
  "subject_nets": [
    { "id": 1, "subject": 6, "subject_label": "TYT Matematik",
      "correct": 34, "wrong": 6, "blank": 0, "net": 32.5, "question_count": 40 },
    { "id": 2, "subject": 8, "subject_label": "TYT Fizik",
      "correct": 11, "wrong": 0, "blank": 3, "net": 11.0, "question_count": 7 }
  ]
}
```

> **Net girişi doğru/yanlış ile yapılır.** Öğrenci ders başına **`correct`** (doğru) ve
> **`wrong`** (yanlış) sayısını gönderir. Sunucu türetir:
> - `net = correct - wrong/4` (2 ondalık, salt-okunur)
> - `blank = question_count - correct - wrong` (boş; ders soru sayısı biliniyorsa, yoksa null)
> - `question_count` dersin sınavdaki soru sayısı (maks. doğru) — salt-okunur.
>
> Validasyon: `correct + wrong` dersin `question_count`'unu **aşamaz** (400).

## Endpoint'ler
```
GET  /api/exams/                 → öğrenci: kendi denemeleri
                                   rehber: öğrencilerininki (?student=<id> ile filtre)
     ?source=personal|institutional ile süzülebilir (E1); bilinmeyen değer
                                   sessizce yok sayılır (boş liste dönmez)
POST /api/exams/     (öğrenci)   → deneme + netleri birlikte oluşturur
     {
       "exam_type": "tyt", "source"?: "personal|institutional", "name": "...",
       "exam_date": "YYYY-MM-DD",
       "subject_nets": [ { "subject": <id>, "correct": 34, "wrong": 6 }, ... ]
     }
     ← 201 deneme objesi (total_net hesaplanmış)
GET    /api/exams/{id}/  (sahibi öğrenci + rehberi)
PATCH  /api/exams/{id}/  (yalnızca sahibi öğrenci) — subject_nets gönderilirse
                          eski netler silinip yenileri yazılır (tam değişim)
DELETE /api/exams/{id}/  (yalnızca sahibi öğrenci)
```

## Hatalar
| Kod | Durum |
|-----|-------|
| `400` | Aynı ders iki kez → `subject_nets`; negatif `correct`/`wrong`; `correct+wrong > question_count`; eksik `exam_date` |
| `401` | Token yok/geçersiz |
| `403` | Rehberin deneme girmesi/düzenlemesi; başka öğrencinin denemesi |
| `404` | Deneme yok |

## Kişisel / kurumsal ayrımı (E1)

`source` denemenin **nerede çözüldüğünü** söyler:

- `personal` (varsayılan) — öğrenci evde tek başına çözdü.
- `institutional` — kurum geneli sınav: gözetimli ve herkesle aynı koşulda.

İkisi aynı kefeye konulamadığı için istatistikte ayrıştırılabilsin diye tutulur.
Sonradan `PATCH` ile düzeltilebilir (yanlış işaretlenmişse). `400` dönen geçersiz
bir değer verilirse deneme kaydedilmez.

## Not
- `subject` alanına herhangi bir ders id'si verilebilir (sınıf kısıtı yok);
  frontend `/api/subjects/` ile öğrenciye uygun listeyi gösterir.
