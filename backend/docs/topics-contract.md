# Rehberim — Konular API Kontratı

> **Sürüm:** v1.1 · **Durum:** TASLAK · **Tarih:** 2026-08-29
>
> Ders + sınıf bazlı **konu kataloğu** ve öğrencinin her konudaki **ilerlemesi**.
> Auth: tüm uçlar `Authorization: Bearer <access>` ister.

---

## Kavram

- **Konu (`Topic`)** — referans/katalog verisi: bir dersin belirli bir sınıftaki konusu.
  Ör. (Matematik, 10) → "Kombinasyon". Her (ders, sınıf) ikilisinin kendine has konu
  listesi vardır. Katalog admin/seed ile yönetilir; kullanıcı **oluşturmaz**, yalnızca okur.
- **Konu İlerlemesi (`TopicProgress`)** — öğrencinin tek bir konudaki durumu + o konuda
  çözdüğü test sayısı. Öğrenci **oluşturur/günceller/siler**; rehberi ve velisi salt-okur.

> `subject`, mevcut **Subject** kaydıdır (`GET /api/subjects/`). İki tür konu vardır:
> - **Okul dersleri** (category=okul): konular sınıf (`grade` = `9`·`10`·`11`·`12`)
>   + müfredat boyutunda ayrılır. 9/10/11. sınıf öğrencilerinin gördüğü set.
> - **Sınav dersleri** (category=tyt/ayt): 12. sınıf + mezunların gördüğü set. Bunlar
>   sınıfa değil sınav kapsamına ait düz listelerdir; seed'de tümü `curriculum=eski`
>   ve `grade=12` kovasına konur, listeleme `order` ile sıralanır. Öğrenci bu konuları
>   ders bazında (`?subject=`) grade **vermeden** çeker; curriculum otomatik `eski` olur.

## Müfredat (`curriculum`)
YKS geçiş döneminde iki set konu yürürlükte:
- `eski`   — Mevcut müfredat (bu yılki sınav) → **12. sınıf ve mezunlar**.
- `maarif` — Türkiye Yüzyılı Maarif Modeli (sonraki sınavlar) → **9/10/11. sınıf**.

`GET /api/topics/`'te `curriculum` verilmezse ve istek bir öğrenciden geliyorsa,
öğrencinin sınıfına göre **otomatik** seçilir (`Student.curriculum`). Rehber/veli için
varsayılan yoktur; gerekirse `?curriculum=` ile belirtilir. Seed'de **10 okul dersi ×
9-12. sınıf** için iki müfredatın da konuları vardır (Felsefe 9/12 her iki müfredatta
da boştur). İngilizce'nin konusu seed'de yoktur. Ayrıca **10 TYT + 12 AYT dersi** için
sınav konu kataloğu seed'lidir (yalnızca `curriculum=eski`, ÖSYM YKS güncel programı).

## Durum (`status`)
`baslanmadi` (başlanmadı) · `devam` (biraz = devam ediyor) · `tamamlandi` (bitti)

---

## Konu kataloğu (Topic)

```
GET /api/topics/?subject=<id>&grade=<9-12>&curriculum=<eski|maarif>  → filtreli konu listesi
    (curriculum verilmezse öğrencide sınıfına göre otomatik uygulanır)
```
Öğrenci isteğinde her konuya kendi ilerlemesi **gömülü** gelir (Konular sayfası tek
çağrıda dolsun diye):
```json
{
  "id": 2,
  "subject": 24,
  "subject_label": "Matematik",
  "grade": "10",
  "grade_display": "10. Sınıf",
  "curriculum": "maarif",
  "curriculum_display": "Maarif Modeli",
  "name": "Kombinatorik Sayma ve Olasılık",
  "order": 1,
  "my_progress": {          // yalnızca öğrenci isteğinde; rehber/velide null
    "id": 5,                // ilerleme kaydı yoksa null (henüz işaretlenmemiş)
    "status": "tamamlandi",
    "tests_solved": 8
  }
}
```

## Konu ilerlemesi (TopicProgress)

### İlerleme objesi
```json
{
  "id": 5,
  "student": 7,                 // sunucuda atanır (salt-okunur)
  "student_name": "Ali Yılmaz",
  "topic": 2,
  "topic_name": "Kombinasyon",
  "subject_label": "Matematik",
  "grade": "10",
  "status": "tamamlandi",       // baslanmadi | devam | tamamlandi
  "status_display": "Tamamlandı",
  "level": 3,                   // konu hâkimiyet seviyesi 1-5 (1 en düşük, 5 en yüksek)
  "tests_solved": 8,            // o konuda çözülen test sayısı (efor)
  "created_at": "...", "updated_at": "..."
}
```

**`level` (Konu Takibi):** 1-5 arası hâkimiyet seviyesi. Kayıt yoksa kavramsal olarak
**1** (en düşük) kabul edilir — öğrenci yaratılınca satırlar önceden üretilmez. Renk
eşlemesi frontend'de: 1🔴 2🟠 3🟡 4🟢(açık) 5🟩(koyu). **Rehber öğrencisi için girer/düzenler.**
Ayrıca öğrenci bir **kitap konusunu "tamamlandı"** yapınca ilgili `TopicProgress.level`
otomatik **+1** yükselir (tek yönlü, tavan 5; bkz. `library-contract.md`).

### Endpoint'ler
```
GET  /api/topic-progress/        → öğrenci: kendine ait; rehber ve veli: ilgili
                                   öğrencininki (ikisi de ?student= ile daraltır)
     ?student=<id>  (rehber)     ?subject=<id>  ?grade=<9-12>   → ek filtreler
POST /api/topic-progress/  (öğrenci veya rehber) → { "topic": <id>, "level": 4, ... }
     · Öğrenci kendi adına; REHBER `"student": <id>` (kendi öğrencisi) ekler.
     · Aynı konuya tekrar POST → mevcut kaydı GÜNCELLER (upsert; yeni kayıt açmaz).
     · `add_tests` (opsiyonel, write-only): `tests_solved`'ı bu kadar ARTIRIR.
     ← 201 ilerleme objesi
GET    /api/topic-progress/{id}/  (sahibi öğrenci + rehberi + veli)
PATCH  /api/topic-progress/{id}/  (sahibi öğrenci veya rehberi) — ör. { "level": 5 }
DELETE /api/topic-progress/{id}/  (sahibi öğrenci veya rehberi)
```

---

## Hatalar
| Kod | Durum |
|-----|-------|
| `400` | Eksik/hatalı alan; geçersiz `status`/`grade`; negatif `add_tests` |
| `401` | Token yok/geçersiz |
| `403` | Öğrenci-dışı rol ilerleme oluşturması; sahibi-olmayanın düzenlemesi/silmesi |
| `404` | Kayıt yok |

## Notlar
- `student` istemciden alınmaz; giriş yapan öğrenciye otomatik atanır.
- Her (öğrenci, konu) için tek ilerleme kaydı vardır (`unique_together`). "İşaretle"
  akışında POST kullanmak yeterli — kayıt varsa güncellenir.
- Konu kataloğu (`Topic`) API'den oluşturulmaz; admin panelinden veya data
  migration'la yönetilir.
