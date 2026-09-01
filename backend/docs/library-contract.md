# Rehberim — Kitaplık API Kontratı

> **Sürüm:** v1.1 · **Durum:** TASLAK · **Tarih:** 2026-08-29
>
> Öğrencinin **kitaplığı**. Auth: tüm uçlar `Authorization: Bearer <access>` ister.
> Kitabı **öğrenci** ekler/düzenler/siler; rehberi yalnızca görür.
> **Veli kitaplığı görmez** (kullanıcı kararı, 29 Ağu 2026 — E3).

---

## Roller
- **Öğrenci:** kendi kitaplığına kitap ekler / görür / düzenler / siler.
- **Rehber:** öğrencisinin kitaplarını **yalnızca görür** (salt-okur).
- **Veli:** kitaplığı **hiç görmez** — liste boş döner, detayda `403`.

## Kitap türleri (`kind`)
| Değer | Anlam | İstenen alanlar |
|-------|-------|-----------------|
| `ders`  | Derse ait çalışma kitabı | `subject` **zorunlu** (tür+dersi kapsar, ör. "TYT Matematik") + `book_format` **zorunlu** + `publisher` (opsiyonel) |
| `okuma` | Ders dışı okuma kitabı (ör. "Suç ve Ceza") | `title` **zorunlu** + `author` (opsiyonel) |

> `subject`, mevcut **Subject** kaydıdır ve **tür (TYT/AYT/okul) + ders**'i birlikte
> tutar — ayrı bir "tür" alanı yoktur. Dersler `GET /api/subjects/` ile alınır.

> **Yayınevi (`publisher`)** serbest metindir ama dropdown'ı `GET /api/publishers/`
> besler (en çok kullanılan 68 yayınevi). Öğrenci listede olmayan bir yayınevini
> serbestçe de yazabilir. Uç: `[{ "id": 1, "name": "ÜçDörtBeş (345) Yayınları" }, ...]`.

### Kitap formatı (`book_format`, yalnızca `kind=ders`)
`paragraf` · `konu_anlatimi` · `soru_bankasi` · `deneme`

### Durum (`status`)
`baslanmadi` (varsayılan) · `devam` · `tamamlandi`

> **İleride:** Bir kitabın üniteleri ayrı bir model (`BookUnit`) ile tutulacak;
> öğrenci her üniteyi tamamlandı/devam/başlanmadı işaretleyecek ve tamamlanma
> yüzdesi oradan hesaplanacak. Şimdilik ilerleme kitap seviyesinde `status` ile tutulur.

## Kitap objesi
```json
{
  "id": 1,
  "student": 7,                    // sunucuda atanır (salt-okunur)
  "student_name": "Ali Yılmaz",
  "kind": "ders",                  // ders | okuma
  "title": "",                     // okuma'da zorunlu; ders'te opsiyonel kitap adı
  "label": "TYT Matematik 345 Soru Bankası",  // gösterim etiketi (salt-okunur, sunucu üretir)
  "description": "",               // opsiyonel
  "status": "baslanmadi",          // baslanmadi | devam | tamamlandi
  "subject": 6,                    // yalnızca ders; okuma'da null
  "subject_label": "TYT Matematik",// subject varsa etiketi (salt-okunur)
  "publisher": "345",              // yalnızca ders; opsiyonel
  "book_format": "soru_bankasi",   // yalnızca ders
  "author": "",                    // yalnızca okuma; opsiyonel
  "created_at": "...", "updated_at": "..."
}
```

## Endpoint'ler
```
GET  /api/books/                 → öğrenci: kendi kitapları (veli: boş liste)
                                   rehber: öğrencilerininki (?student=<id> ile filtre)
POST /api/books/     (öğrenci)   → ders:  { "kind": "ders", "subject": <id>,
                                     "book_format": "soru_bankasi", "publisher": "345"? }
                                   okuma: { "kind": "okuma", "title": "Suç ve Ceza",
                                     "author": "Dostoyevski"? }
                                   ← 201 kitap objesi (student otomatik atanır)
GET    /api/books/{id}/  (sahibi öğrenci + rehberi; veli 403) — yanıt `topics` içerir
PATCH  /api/books/{id}/  (yalnızca sahibi öğrenci) — ör. { "status": "devam" }
DELETE /api/books/{id}/  (yalnızca sahibi öğrenci)
```

---

## Kitap içi konular (BookTopic) — otomatik doldurulur

Bir **ders kitabı** oluşturulunca backend, kitabın dersine göre içindeki konuları
konu kataloğundan **otomatik doldurur** (`Book.populate_topics()`). Eşleme:

| Kitabın dersi | Alınan konular |
|---|---|
| **TYT** [ders] | O dersin **9. ve 10. sınıf** konuları |
| **AYT** [ders] | O dersin **11. ve 12. sınıf** konuları |
| **Okul** dersi | Öğrencinin **kendi sınıfı** |

Müfredat öğrencinin sınıfına göre (eski/maarif) seçilir. Konular **okul derslerinde**
tutulduğu için sınav dersi adı okul dersine çevrilir (ör. TYT "Türkçe" → "Türk Dili ve
Edebiyatı", AYT "Tarih-1/2" → "Tarih"). Okuma kitabında konu doldurulmaz.

`BookTopic`, `TopicProgress`'ten ayrıdır: bu, konunun **o kitap özelindeki** ilerlemesidir
(öğrencide aynı dersten birden çok kitap olabilir).

### Kitap detayındaki `topics` (nested, salt-okunur)
```json
"topics": [
  {
    "id": 10, "book": 3, "topic": 42,
    "topic_name": "Hücre Bölünmeleri (Mitoz, Eşeysiz Üreme, Mayoz, Eşeyli Üreme)",
    "grade": "10",
    "status": "devam", "status_display": "Devam Ediyor",
    "tests_solved": 3, "order": 3
  }
]
```

### İşaretleme
```
GET   /api/book-topics/{id}/  (sahibi öğrenci + rehberi; veli 403)
PATCH /api/book-topics/{id}/  (yalnızca sahibi öğrenci)
      → { "status": "tamamlandi" }  ya da  { "add_tests": 5 }  (tests_solved += 5)
```
`book`, `topic`, `order` salt-okunurdur; konular otomatik gelir, öğrenci yalnızca
durum/test sayısını günceller.

> **Yan etki:** Bir `BookTopic` "tamamlandı"ya geçtiğinde, öğrencinin o konudaki
> `TopicProgress.level` değeri otomatik **+1** yükselir (tek yönlü, tavan 5). Böylece
> kitapta konu bitirmek Konu Takibi seviyesini besler. Bkz. `topics-contract.md`.

---

## Hatalar
| Kod | Durum |
|-----|-------|
| `400` | Eksik/hatalı alan; `kind=ders`'te `subject` veya `book_format` eksik; `kind=okuma`'da `title` eksik; türe uymayan alan gönderimi (okuma'da subject/publisher/format, ders'te author) |
| `401` | Token yok/geçersiz |
| `403` | Öğrenci-dışı rol oluşturması; sahibi-olmayanın düzenlemesi/silmesi; başkasının kaydına erişim |
| `404` | Kayıt yok |

## Notlar
- `student` istemciden alınmaz; giriş yapan öğrenciye otomatik atanır.
- `subject` ayrı bir "tür/ders" ikilisi değil, tek bir Subject FK'sidir — TYT/AYT/okul
  bilgisini içinde taşır (`GET /api/subjects/` dropdown'undan seçilir).
