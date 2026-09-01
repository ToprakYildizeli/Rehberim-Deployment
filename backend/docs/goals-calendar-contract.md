# Rehberim — Hedefler & Takvim API Kontratı

> **Sürüm:** v1.1 · **Durum:** TASLAK · **Tarih:** 2026-08-29
>
> Öğrencinin kendine koyduğu **hedefler** ve rehberin **kendi takvimi**. Auth:
> tüm uçlar `Authorization: Bearer <access>` ister. Hedefleri öğrenci koyar
> (rehber/veli salt-okur); takvimde uygulama içi randevulaşma yoktur — rehber
> tek taraflı oluşturur, öğrenci (ve velisi) haberdar olur.

---

## Hedefler (Goals)

> **v2 (2026-07-17):** Hedefi artık **öğrenci** koyar (v1'de rehber koyuyordu).
> Hedeflere **tür** (`goal_type`) eklendi. `counselor` alanı kaldırıldı.

### Roller
- **Öğrenci:** kendine hedef ekler / görür / düzenler / siler.
- **Rehber:** öğrencisinin hedeflerini **yalnızca görür**.
- **Veli:** hedefleri **hiç görmez** (E3 kapsam kararı, 29 Ağu 2026) — liste
  boş döner, detayda `403`. Takvim ise veliye **açık** kalır (aşağısı).

### Hedef türleri (`goal_type`)
| Değer | Anlam | İstenen alanlar |
|-------|-------|-----------------|
| `deneme_net` | Deneme neti hedefi | `exam_scope` (tyt/ayt) **zorunlu** + `subject` (opsiyonel; boş = TOPLAM net) + `target_net` **zorunlu** |
| `konu` | Konu bitirme | *(ileride)* Konu listesinden seçim — şimdilik serbest `title` |
| `kitap_bitirme` | Soru/test kitabını bitirme (ör. "TYT Türkçe 345 Yay.") | *(ileride)* Kitap listesinden seçim — şimdilik serbest `title` |
| `kitap_okuma` | Edebiyat kitabı okuma (ör. "Suç ve Ceza") | *(ileride)* Kitap listesinden seçim — şimdilik serbest `title` |

> `konu` / `kitap_*` türlerinin referansları (Konu, Kitap modelleri) sonra eklenecek;
> o zamana kadar bu hedefler `title` ile tutulur.

### Hedef objesi
```json
{
  "id": 1,
  "student": 7,                   // sunucuda atanır (salt-okunur)
  "student_name": "Ali Yılmaz",
  "goal_type": "deneme_net",      // deneme_net | konu | kitap_bitirme | kitap_okuma
  "title": "",                    // konu/kitap'ta serbest metin; deneme'de opsiyonel
  "label": "TYT Toplam 110 net",  // gösterim etiketi (salt-okunur, sunucu üretir)
  "description": "",              // opsiyonel
  "target_date": "2026-09-01",    // opsiyonel hedef tarihi
  "is_achieved": false,
  "order": 0,
  "exam_scope": "tyt",            // yalnızca deneme_net; aksi halde ""
  "subject": null,                // yalnızca deneme_net; null = TOPLAM net
  "subject_label": null,          // subject varsa etiketi (salt-okunur)
  "target_net": 110,              // yalnızca deneme_net
  "created_at": "...", "updated_at": "..."
}
```

### Endpoint'ler
```
GET  /api/goals/                 → öğrenci: kendi hedefleri (veli: boş liste)
                                   rehber: öğrencilerininki (?student=<id> ile filtre)
POST /api/goals/     (öğrenci)   → deneme:  { "goal_type": "deneme_net",
                                     "exam_scope": "tyt", "target_net": 110,
                                     "subject": <id>? }
                                   kitap/konu: { "goal_type": "kitap_okuma",
                                     "title": "Suç ve Ceza" }
                                   ← 201 hedef objesi (student otomatik atanır)
GET    /api/goals/{id}/  (sahibi öğrenci + rehberi; veli 403)
PATCH  /api/goals/{id}/  (yalnızca sahibi öğrenci) — ör. { "is_achieved": true }
DELETE /api/goals/{id}/  (yalnızca sahibi öğrenci)
```

---

## Takvim (Calendar)

Rehberin kişisel takvimi. Bir etkinliğe **`student` bağlanırsa** o etkinlik
görüşme/öğrenci etkinliğidir ve ilgili öğrenci (+ velisi) onu salt-okur görür
(ör. *"Cumartesi 14-15 Ahmet görüşme"*). `student` **boşsa** etkinlik yalnızca
rehberin kişisel notudur (ör. *"Özdebir TYT — 16 Temmuz"*).

### Roller
- **Rehber:** kendi takvimindeki tüm etkinlikleri ekler / görür / düzenler / siler.
- **Öğrenci & Veli:** yalnızca **kendine bağlı** etkinlikleri görür (salt-okur).
  `student` boş etkinlikler onlara görünmez.

### Etkinlik objesi
```json
{
  "id": 1,
  "counselor": 3,                 // sahibi rehber (salt-okunur)
  "student": 7,                   // opsiyonel; null → kişisel not
  "student_name": "Ali Yılmaz",   // student null ise null
  "title": "Görüşme",
  "description": "",              // opsiyonel
  "date": "2026-07-19",
  "start_time": "14:00",          // opsiyonel; null → tüm gün
  "end_time": "15:00",            // opsiyonel (start ile birlikte)
  "is_all_day": false,            // start_time yoksa true (salt-okunur)
  "created_at": "...", "updated_at": "..."
}
```

### Endpoint'ler
```
GET  /api/calendar/              → rehber: kendi takvimi (?student=<id> ile filtre)
                                   öğrenci/veli: kendine bağlı etkinlikler
     ?from=YYYY-MM-DD&to=YYYY-MM-DD  → tarih aralığına göre filtre (opsiyonel)
POST /api/calendar/  (rehber)    → { "title": "...", "date": "YYYY-MM-DD",
                                     "student": <id>?, "start_time": "HH:MM"?,
                                     "end_time": "HH:MM"? }
                                   ← 201 etkinlik objesi (counselor otomatik)
GET    /api/calendar/{id}/  (sahibi rehber + bağlı öğrenci/veli)
PATCH  /api/calendar/{id}/  (yalnızca sahibi rehber)
DELETE /api/calendar/{id}/  (yalnızca sahibi rehber)
```

---

## Hatalar (her iki uç için)
| Kod | Durum |
|-----|-------|
| `400` | Eksik/hatalı alan; deneme neti hedefinde `target_net`/`exam_scope` eksik; deneme dışı türde deneme alanı gönderimi; takvimde `end_time` başlangıçtan önce/eşit; başlangıçsız `end_time` |
| `401` | Token yok/geçersiz |
| `403` | **Hedef:** öğrenci-dışı rol oluşturması, sahibi-olmayanın düzenlemesi/silmesi. **Takvim:** rehber-dışı rol oluşturması-düzenlemesi; rehberin **başka** öğrencisini etkinliğe bağlaması; başkasının kaydına erişim |
| `404` | Kayıt yok |

## Notlar
- **Hedef:** `student` istemciden alınmaz; giriş yapan öğrenciye otomatik atanır.
  `deneme_net` dışındaki türlerde `exam_scope`/`subject`/`target_net` gönderilirse `400`.
- **Takvim:** `student` alanına yalnızca **rehberin kendi öğrencisi** verilebilir; aksi halde `403`.
- Takvimde saat isteğe bağlıdır: saat verilmezse tüm-gün etkinliği (`is_all_day: true`).
  `end_time` verilecekse `start_time` de zorunludur ve `end_time > start_time` olmalı.
