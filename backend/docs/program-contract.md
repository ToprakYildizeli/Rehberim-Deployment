# Rehberim — Haftalık Program & Görevler API Kontratı

> **Sürüm:** v3.6 · **Durum:** TASLAK · **Tarih:** 2026-08-29
>
> **v3.6 (E3, veli erişimi):** uyum objesine `completed_hours` eklendi —
> `study_hours` **planlanan**, `completed_hours` **gerçekten çalışılan** saattir;
> veli ekranındaki "bu hafta kaç saat çalıştı" ikincisidir. Ayrıca veli artık
> `GET /api/programs/?student=` ve `GET /api/topic-progress/?student=` ile tek
> çocuğa daraltabiliyor. Alan **eklendi**, hiçbiri değişmedi — geriye uyumlu.
>
> Rehberin oluşturduğu, öğrencinin görüp doğrudan düzenlediği program ve içindeki
> görevler. Auth için bkz. `auth-contract.md` — tüm uçlar
> `Authorization: Bearer <access>` ister.
>
> **v3 değişiklikleri (yol haritası A1 + A3):**
> - Program uzunluğu esnek: `day_count` (yeni, varsayılan 7). `end_date` bundan türetilir.
> - Aynı öğrencinin iki programı **tarih aralığı olarak örtüşemez** (eski
>   "aynı başlangıç günü tekil" kısıtının yerini aldı).
> - Görevde **blok türü**: `kind` (`study`/`external`/`exam`) + `exam_scope`
>   (genel TYT/AYT denemesi) + salt-okunur `counts_as_study`.
> - `/programs/assign/` çakışan bir aralığa sessizce kaymaz; `400` döner.
>
> **v3.1:** `/api/subjects/` alan bazlı süzme kazandı (`?student=&scope=field`) —
> ders programı tahtasının varsayılan ders satırları için.
>
> **v3.2 (yol haritası A4 — süre hafızası):** yeni salt-okunur uç
> `GET /api/block-durations/`. Rehberin bir blok kombinasyonunda en son kullandığı
> süreyi döndürür; blok formunda varsayılanı doldurmak için. Yazma ucu **yoktur** —
> hafıza görev kaydedilirken kendiliğinden güncellenir. Mevcut alanlar değişmedi,
> bu ekleme geriye dönük uyumludur.
>
> **v3.3 (yol haritası B1 — haftalık onay):** programa onay alanları
> (`is_approved`, `is_finished`, `approved_at`, `approved_by`, `approved_by_name`,
> hepsi salt-okunur) ve yeni uç `POST/DELETE /api/programs/{id}/approve/` eklendi.
> İki **davranış değişikliği** var:
> - **Veli** artık programları görüyor — ama **yalnızca onaylanmışları**.
> - **Öğrenci**, onaylanmış bir programın görevlerine artık yazamıyor (`403`).
> Rehber ve öğrenci için onaysız programlarda hiçbir şey değişmedi.
>
> **v3.4 (yol haritası B2 — uyum yüzdesi):** program objesine salt-okunur
> `compliance` özeti ve yeni uç `GET /api/programs/compliance/?student=<id>`
> eklendi. Uyum **süre** üzerinden hesaplanır. Geriye dönük uyumlu ekleme.
>
> **v3.5 (yol haritası E2):** yeni salt-okunur uç `GET /api/study-stats/` —
> öğrencinin tamamladığı çalışmanın saat toplamı ve TYT/AYT · ders dağılımı.
> Mevcut alanlar değişmedi.

## 1. Temel kavramlar

- **Program** `start_date`'ten (görüşme günü) başlar ve `day_count` gün sürer:
  `end_date = start_date + day_count - 1` (dahil). Varsayılan `day_count` 7'dir,
  1–31 arası olabilir. Rehber Salı günü, geçmiş Pazartesiden başlayan 5 günlük bir
  program da açabilir — `start_date` geçmiş bir tarih olabilir.
- Aynı öğrencinin programları **örtüşemez**; çakışan aralık `400` döner.
- Program iki **tipte** olur (`schedule_type`):
  - `timed` (**saatli**): görevler saat + süreyle planlanır (çalışma blokları).
  - `untimed` (**saatsiz**): görevler sadece bir güne konur ("bugün şunlar").
- **Görev (Task)** = bir program bloğu; bir güne (`date`) eklenir. Saatli programda
  `start_time` + `duration_minutes` zorunlu; saatsizde girilmez.
- **Blok türü (`kind`)** bloğun ne olduğunu söyler:
  - `study` (varsayılan) — normal çalışma: DERS (`subject`) + METOD (`task_type`).
  - `external` — okul, dershane, antrenman, doktor gibi çalışma **dışı** meşguliyet.
    Programda yer kaplar ve saatini bloke eder, ama **çalışma saatine sayılmaz**.
  - `exam` — deneme. Ders bazlı (`subject`) ya da **genel** (`exam_scope`: `tyt`/`ayt`,
    ders seçilmeden).
- **Taşıma / sıralama (drag & drop):** `order` = görevin **gün içindeki 0-based
  pozisyonu**. Bir görevi taşımak/araya bırakmak = `PATCH /api/tasks/{id}/` ile
  `date` ve/veya `order` göndermek. **Kaydırmayı backend yapar** — hedef pozisyona
  yer açar, o günün diğer görevlerini otomatik kaydırır, ayrıldığı günde boşluğu
  kapatır. Frontend yalnızca "şu güne, şu pozisyona koy" der; tek tek order
  güncellemek gerekmez.
- Roller: **rehber** program açar/siler, program-seviyesini düzenler; **öğrenci ve
  rehber** görev ekler/düzenler/taşır/siler; öğrenci görevleri tamamlandı işaretler.

## 2. Referans veri (dropdown'lar)

```
GET /api/subjects/       → DERS listesi (öğrenci çağırırsa sınıfına göre filtreli)
GET /api/subjects/?student=<id>&scope=field   (rehber, kendi öğrencisi)
GET /api/subjects/?scope=field                (öğrenci, kendisi)
    → öğrencinin **alanına düşen** dersler: tüm TYT + alanının AYT dersleri
      (say → Mat/Geo/Fiz/Kim/Biy · ea → Mat/Geo/Edebiyat/Tarih-1/Coğrafya-1 ·
       söz → Edebiyat/Tarih-1,2/Coğrafya-1,2/Felsefe/Din K.)
    → Bir **kısıt değil**, makul bir başlangıç kümesi: ders programı tahtasında
      hangi ders satırlarının varsayılan açılacağını belirler. Öğrenci alanı
      dışından da ders çalışabilir; `scope` verilmezse süzgeç uygulanmaz.
    → Başka bir rehberin öğrencisi istenirse `404`.
GET /api/task-types/     → METOD listesi
GET /api/block-durations/ → (yalnızca rehber) süre hafızası; bkz. §9
GET /api/students/       → (yalnızca rehber) kendi öğrencileri; program açarken id buradan
    ← [ { "id": 8, "full_name": "Ali Yılmaz", "grade": "12",
          "grade_display": "12. Sınıf", "study_field": "say" } ]
```

## 3. Program objesi

```json
{
  "id": 1,
  "student": 4,
  "student_name": "Ali Yılmaz",
  "counselor": 2,
  "start_date": "2026-07-15",
  "day_count": 7,                 // 1-31, varsayılan 7
  "end_date": "2026-07-21",       // salt-okunur: start_date + day_count - 1
  "schedule_type": "timed",       // "timed" | "untimed"
  "note": "",
  "tasks": [ { ...bkz. §4 } ],

  // --- Haftalık onay (§10) · hepsi salt-okunur ---
  "is_approved": false,           // approved_at doluysa true
  "is_finished": true,            // end_date geçti mi (onay ancak o zaman verilebilir)
  "approved_at": null,            // ISO zaman damgası ya da null
  "approved_by": null,            // onaylayan rehberin id'si
  "approved_by_name": null,       // gösterim için ad

  // --- Uyum özeti (§11) · salt-okunur ---
  "compliance": {
    "percent": 75,                // boş programda null
    "basis": "duration",          // "duration" | "count" | "empty"
    "total_minutes": 240,
    "completed_minutes": 180,
    "total_tasks": 4,
    "completed_tasks": 3,
    "study_hours": 4.0,           // PLANLANAN çalışma (pencerenin kendisi kadar)
    "completed_hours": 3.0,       // GERÇEKTEN çalışılan saat (v3.6, E3)
    "weekly_hours": 4.0           // haftalık hıza çevrilmiş hâli
  },

  "created_at": "...", "updated_at": "..."
}
```

## 4. Görev (Task) objesi

```json
{
  "id": 10,
  "program": 1,
  "subject": 6, "subject_label": "TYT Matematik",     // DERS (opsiyonel)
  "task_type": 3, "task_type_name": "Konu Çalışması",  // METOD (opsiyonel)
  "book": 29, "book_label": "TYT Fizik Palme Soru Bankası",  // KAYNAK KİTAP (opsiyonel)
  "kind": "study",                 // "study" | "external" | "exam" — varsayılan "study"
  "exam_scope": "",                // "" | "tyt" | "ayt" — yalnız genel deneme bloğunda
  "title": "20 soru",
  "description": "",
  "date": "2026-07-16",            // start_date..end_date aralığında
  "start_time": "09:00:00",        // saatli programda dolu, saatsizde null
  "duration_minutes": 60,          // saatli programda dolu, saatsizde null
  "end_time": "10:00:00",          // otomatik (start+süre); saatsizde null
  "is_completed": false,
  "counts_as_study": true,         // salt-okunur: kind != "external"
  "created_by": 5,
  "order": 0                       // gün içi pozisyon (0-based); POST'ta verilmezse sona eklenir
}
```

### Blok türüne göre alan kuralları

| `kind` | `subject` / `task_type` / `book` | `exam_scope` | `title` | Çalışma saatine sayılır |
|---|---|---|---|---|
| `study` (varsayılan) | serbest | **boş olmalı** | opsiyonel | ✅ |
| `external` | **boş olmalı** | **boş olmalı** | **zorunlu** | ❌ |
| `exam` | `subject` **veya** `exam_scope` (ikisi birden değil) | ders yoksa zorunlu | opsiyonel | ✅ |

Örnek — genel TYT denemesi (ders seçmeden):

```json
{ "kind": "exam", "exam_scope": "tyt", "date": "2026-07-18",
  "start_time": "09:00", "duration_minutes": 135 }
```

Örnek — antrenman (çalışma saatine sayılmaz, ama o saati bloke eder):

```json
{ "kind": "external", "title": "Antrenman", "date": "2026-07-18",
  "start_time": "17:00", "duration_minutes": 90 }
```

## 5. Endpoint'ler

### Programlar
```
GET  /api/programs/             → rol bazlı liste (öğrenci: kendi · rehber: öğrencileri)
POST /api/programs/             (rehber)
     → { "student": <id>, "start_date": "YYYY-MM-DD", "day_count"?: 7,
         "schedule_type": "timed|untimed", "note"? }
GET  /api/programs/{id}/        (katılımcı) → program + görevler (tasks)
PATCH/DELETE /api/programs/{id}/ (yalnızca rehber) → "start_date"/"day_count" değiştirilebilir
GET  /api/programs/current/     (öğrenci) → bugünü kapsayan güncel program
POST   /api/programs/{id}/approve/ (yalnızca sahibi rehber) → haftayı onayla   (§10)
DELETE /api/programs/{id}/approve/ (yalnızca sahibi rehber) → onayı geri al    (§10)
GET    /api/programs/compliance/?student=<id>  → uyum geçmişi + dönemsel özet (§11)
GET    /api/study-stats/?student=<id>          → çalışma saati + dağılım       (§12)
```

`GET /api/programs/` **veli** için de çalışır: çocuklarının **onaylanmış**
programlarını döndürür. Onaysız program veliye ne listede ne de tekil `GET`'te
görünür (`403`). Birden çok çocuğu olan veli `?student=<id>` ile tek çocuğa
daraltabilir (v3.6).

`PATCH` ile pencere daraltılıp genişletilebilir; sonuç başka bir programla örtüşürse `400`.
Yeni pencerenin **dışında kalacak bir görev varsa `PATCH` reddedilir**
(`{"day_count": [...]}`) — görev öksüz kalmasın diye. Önce görevler taşınmalı veya
silinmeli. (Aynı kural `start_date` kaydırmak için de geçerlidir.)

### Görevler (Task)
```
GET  /api/programs/{id}/tasks/  (katılımcı) → o programın görevleri
POST /api/programs/{id}/tasks/  (rehber veya öğrenci)
     saatli:  { "kind"?, "exam_scope"?, "subject"?, "task_type"?, "book"?, "title"?, "date", "start_time", "duration_minutes", "order"? }
     saatsiz: { "kind"?, "exam_scope"?, "subject"?, "task_type"?, "book"?, "title"?, "date", "order"? }
     → "book" verilirse programın öğrencisine ait olmalı (değilse 400); ders akışı yerine
       doğrudan kütüphaneden eklemede kullanılır, dersi kitaptan türetilir.
     → "order" verilirse o pozisyona eklenir (sonrakiler kayar); verilmezse günün sonuna
PATCH  /api/tasks/{id}/          (katılımcı) → düzenle / taşı-sırala ({"date"?, "order"?}) /
                                   tamamla ({"is_completed": true})
                                   → "order"/"date" değişince backend gün içi sırayı otomatik kaydırır
DELETE /api/tasks/{id}/          (katılımcı)
```

## 6. Hatalar

| Kod | Durum |
|-----|-------|
| `400` | Program penceresi mevcut bir programla örtüşüyor → `{"start_date": [...]}`; `day_count` 1–31 dışında |
| `400` | `date` pencere dışı → `{"date": [...]}`; saatli programda saat eksik / saatsizde saat verildi / süre ≤ 0 / saat çakışması → `{"start_time": [...]}` |
| `400` | Blok türü kuralı ihlali → `{"kind": [...]}` (dış bloğa ders/metod/kitap), `{"title": [...]}` (dış blokta başlık yok), `{"exam_scope": [...]}` (deneme bloğunda ne ders ne kapsam; ikisi birden; çalışma bloğunda kapsam) |
| `401` | Token yok/geçersiz |
| `400` | Pencere daraltma yeni pencereye sığmayan görev bırakıyor → `{"day_count": [...]}` |
| `400` | Program bitmeden onaylanmaya çalışıldı → `{"detail": "..."}` |
| `403` | Başka öğrencinin programı; öğrencinin program açması/silmesi |
| `403` | Öğrenci **onaylanmış** programın görevini değiştirmeye/silmeye/eklemeye çalıştı |
| `403` | Veli onaysız programa erişmeye ya da herhangi bir programa yazmaya çalıştı |
| `404` | Program/görev yok |

## 7. Notlar

- **Saat çakışması yalnızca saatli programda** kontrol edilir: aynı gün zaman aralığı
  çakışan iki görev olamaz (bir saatte tek görev). Bitişik görevler (09:00–10:00 ve
  10:00–11:00) serbest. **Dış meşguliyet blokları da bu kontrole girer** — öğrenci
  okuldayken/antrenmandayken aynı saate çalışma bloğu konamaz.
- Ders ↔ öğrenci sınıfı uyumu **zorlanmaz** (her ders kabul edilir); frontend
  `/api/subjects/` ile uygun listeyi gösterir.
- **Program pencereleri örtüşemez.** Aynı öğrenci için `[start_date, end_date]`
  aralıkları kesişen iki program olamaz; ihlal `400` döner. (v2'deki
  "aynı `start_date` için tek program" kısıtı kaldırıldı — uzunluk değişken olduğu
  için tek başına yetmiyordu.)
- **Çalışma saati hesabı** `counts_as_study` üzerinden yapılır: `external` bloklar
  haftalık toplam çalışma saatine girmez.

## 8. Program Şablonları + Atama (rehber)

Rehber, tekrar kullanmak için **isimli şablon program** ("Sayısal 1" gibi) saklar; şablon
öğrenciden/tarihten bağımsızdır (görevler `weekday` 0-6 ile tutulur). Atama sırasında şablon
somut bir haftaya (`WeeklyProgram` + `Task`) materyalize edilir.

### Şablon objesi
```json
{
  "id": 1, "name": "Sayısal 1", "schedule_type": "timed",
  "student": null, "student_name": null, "auto_apply": false,
  "tasks": [
    { "id": 5, "subject": 6, "subject_label": "TYT Matematik", "task_type": 1,
      "task_type_name": "Test", "book": null, "book_label": null,
      "kind": "study", "exam_scope": "", "title": "",
      "weekday": 0, "start_time": "09:00:00", "duration_minutes": 60, "order": 0 }
  ],
  "created_at": "...", "updated_at": "..."
}
```
`weekday`: 0=Pazartesi … 6=Pazar. Şablon görevleri de `kind`/`exam_scope` taşır ve
§4'teki blok türü kurallarına tabidir.

### Şablon uçları (yalnız rehber; herkes yalnızca kendi şablonlarını görür)
```
GET  /api/program-templates/            → rehberin şablonları
POST /api/program-templates/            → { name, schedule_type, student?, auto_apply?, tasks:[{subject,task_type,book?,title?,weekday,start_time?,duration_minutes?,order?}] }
GET/PATCH/DELETE /api/program-templates/{id}/   (sahibi rehber)
```

### Rutin (tekrarlayan program)

Bir şablona **öğrenci** bağlanıp `auto_apply` açılırsa o şablon artık o öğrencinin
**rutinidir**: öğrenciye `POST /api/programs/` ile yeni bir hafta açıldığında rutinin
görevleri o haftaya kendiliğinden materyalize edilir.

```
POST /api/program-templates/
  { "name": "Hafta rutini", "student": 3, "auto_apply": true, "tasks": [...] }
```

Kurallar:

- `student` boş → **genel şablon**; yalnızca `/programs/assign/` ile elle atanır (eski davranış aynen sürüyor).
- `auto_apply: true` **öğrenci ister** — öğrencisiz gönderilirse `400`.
- Öğrenci başına **en fazla bir** otomatik rutin olabilir; ikincisi `400` döner.
- Rutin yalnızca rehberin **kendi** öğrencisi için tanımlanabilir.
- Rutin *o anki* hâliyle uygulanır: sonradan düzenlenmesi **zaten açılmış haftaları
  değiştirmez**, yalnızca bundan sonra açılacak haftaları etkiler.
- `/programs/assign/` ile açıkça bir plan atanırken rutin **ayrıca uygulanmaz** (çift yazma olmaz).
- Öğrenci, o haftaya düşen bir rutin görevini silebilir; bu **rutini bozmaz**, sonraki hafta yine gelir.

### Rutini kim kurar?

**Hem rehber hem öğrenci.** Aynı uçlar iki role de açıktır; rol ne görüldüğünü ve
ne yazılabileceğini belirler:

| | Görür | Oluşturur |
|---|---|---|
| **Rehber** | Kendi genel şablonları + **öğrencilerinin rutinleri** | Genel şablon · kendi öğrencisi için rutin |
| **Öğrenci** | Yalnızca **kendi** rutinleri | Yalnızca kendi rutini |
| **Veli** | — (`403`) | — |

- Öğrenci `POST` ederken gövdedeki `student` **yok sayılır**, kayıt her zaman kendisine
  bağlanır; başka bir öğrenci id'si gönderirse `400`. Öğrenci genel şablon oluşturamaz.
- Öğrencinin kurduğu rutin `counselor` alanına **öğrencinin rehberi** yazılır, böylece
  rehber onu listesinde görür. Öğrenci henüz bir rehbere bağlı değilse `counselor` boş kalır.
- Başkasının rutinine erişim `404` (kayıt zaten görünür kümede değildir).
- Ad benzersizliği: rutinlerde **öğrenci içinde**, genel şablonlarda **rehber içinde**.
  Aynı rehberin iki öğrencisi rutinine aynı adı verebilir.

**Mobil not:** Rutin **görüntülemek** için ayrı uç yoktur — görevler normal `Task` olarak
üretildiğinden `/programs/` ve `/programs/current/` üzerinden zaten görünür. Öğrencinin
rutini *kurabilmesi* için ise `/program-templates/` uçlarına bağlanan bir ekran gerekir.

| Durum | Ne zaman |
|---|---|
| `400` | `auto_apply` açık ama `student` yok · öğrenci başka rehbere ait · öğrenci başkası adına rutin kurmaya çalıştı · zaten bir otomatik rutin var · ad çakışması |
| `403` | Veli şablon uçlarına erişmeye çalışırsa |
| `404` | Başkasının şablonuna/rutinine erişim |

### Atama
```
POST /api/programs/assign/   (rehber)
  { "student": <id>, "start_date"?: "YYYY-MM-DD", "day_count"?: 7,
    "template": <id>   |   "tasks": [ {weekday,start_time,duration_minutes,subject,task_type,book?,kind?,exam_scope?,title?} ],
    "schedule_type"?: "timed|untimed" }
  → 201 oluşturulan WeeklyProgram (görevleri weekday→tarih eşlenmiş)
```
- `start_date` **verilmezse**: öğrenciye program atanmamış ilk gün (son programın
  bitişinden sonraki gün; geçmişte kalıyorsa **bugün**). Hiç program yoksa bugün.
- `day_count` verilmezse **7**.
- `start_date` **açıkça verilir ve mevcut bir programla örtüşürse** istek sessizce
  kaydırılmaz — `400` `{"start_date": [...]}` döner. (v2'de otomatik +7 gün kayıyordu.)
- `template` verilirse görevler ondan; yoksa `tasks` listesinden alınır.
- `weekday`, hedef pencerenin uygun gününe çevrilir. **Pencereye düşmeyen günler
  atlanır**: 5 günlük Pzt–Cum programında şablonun Cumartesi bloğu yazılmaz. Aynı
  kural rutinin otomatik uygulanmasında da geçerlidir.

### Hatalar (şablon/atama)
| Kod | Durum |
|-----|-------|
| `400` | `template` de `tasks` de yok; geçersiz `student`/alan; blok türü kuralı ihlali; hedef aralık örtüşüyor |
| `403` | Öğrenci-dışı rol; başka öğrenciye atama; başka rehberin şablonu |

---

## 9. Süre hafızası (A4)

Rehberin bir blok kombinasyonunda **en son kullandığı süre**. Amaç, blok formunda
süreyi elle girmeyi tekrarlatmamak: hoca bir öğrenciye "TYT Türkçe → Test →
Paragraf = 20 dk" dediyse, aynı bloğu **başka bir öğrenciye** kurarken de 20 dk
varsayılan gelir.

**İki kritik kural:**

1. Hafıza **rehber özelinde**dir, öğrenci özelinde değil. Öğrenci başına satır açılmaz.
2. Hafıza **konu kombinasyonuna** özeldir: anahtar `(ders, metod, konu)` üçlüsüdür.
   "Matematik denemesi 1 saat" demek, "Matematik soru çözümü de 1 saat" demek
   değildir. Konu, görevin `title` metnidir (web'de `/api/topics/` kataloğundan
   seçilir); **konusuz blok da kendi başına bir kombinasyondur** (`topic: ""`).

### Okuma

```
GET /api/block-durations/     (yalnızca rehber; öğrenci/veli → 403)
  ← [ { "subject": 1, "task_type": 1, "topic": "Paragraf",
        "duration_minutes": 20, "updated_at": "2026-08-23T12:53:32Z" } ]
```

Rehber yalnızca kendi hafızasını görür. Web bunu sayfa açılışında bir kez çekip
`(ders, metod, konu) → dakika` haritası kurar; alanlar değiştikçe süre alanını doldurur.

### Yazma

**Yazma ucu yoktur.** Hafıza, görev `POST`/`PATCH` edilirken sunucuda sessizce
güncellenir (son kullanılan kazanır). Kurallar:

- Yalnızca **rehber** yazar. Öğrenci kendi görevini kaydettiğinde (ya da bir görevi
  "tamamlandı" işaretlediğinde) hocanın varsayılanları değişmez.
- Yalnızca **ders ve metodu belli** bloklar hatırlanır. Dış meşguliyet blokları
  (`kind: "external"`) ve ders seçilmemiş genel deneme blokları (`exam_scope` dolu,
  `subject` boş) kapsam dışıdır.
- Süresi olmayan (saatsiz program) bloklar hatırlanmaz.
- **`PATCH` yalnızca blok tanımı değiştiyse yazar.** Tanım = `(ders, metod, konu, süre)`.
  Bloğu tahtada taşımak (gün/saat/sıra) veya "tamamlandı" işaretlemek hafızaya
  dokunmaz — aksi hâlde eski bir bloğu sürüklemek, o kombinasyon için daha yeni
  girilmiş süreyi geri alırdı. Konu değişikliği yeni kombinasyonu kaydeder.
- Hafıza yazımı görev kaydını **hiçbir koşulda bozmaz**; hatırlanamayan blok sessizce atlanır.

Görev silmek hafızayı silmez — hafıza "bu kombinasyonu en son kaç dakika yaptın"
bilgisidir, programın bir parçası değildir.


## 10. Haftalık onay (B1)

Onay, rehberin *"öğrencinin yaptım dedikleri gerçekten yapılmış"* beyanıdır. Hafta
bitince rehber, öğrencinin tamamlandı işaretlediği görevleri toplantıda kontrol eder,
gerekiyorsa düzeltir ve programı **onaylar**.

### Uç

```
POST   /api/programs/{id}/approve/   → onayla     (200, program objesi döner)
DELETE /api/programs/{id}/approve/   → onayı kaldır (200, program objesi döner)
```

Gövde yok. İkisi de **idempotent**: zaten onaylı bir programı tekrar `POST` etmek
`approved_at`'i değiştirmez, onaysız bir programı `DELETE` etmek hata vermez.

### Kurallar

1. **Kim:** yalnızca programın sahibi rehber (öğrencinin bağlı olduğu rehber).
   Başka rehber, öğrenci ya da veli → `403`.
2. **Ne zaman:** yalnızca **pencere kapandıktan sonra**, yani `is_finished == true`
   (`end_date < bugün`). Son günü bugün olan program henüz onaylanamaz → `400`.
3. **Veli görünürlüğü:** onaysız program veliye **hiç** gösterilmez. Onaydan sonra
   `GET /api/programs/` ve `GET /api/programs/{id}/` velinin çocuğu için çalışır.
   Veli her koşulda **salt-okurdur**.
4. **Onay bir mühürdür:** onaydan sonra **öğrenci** o programın görevlerine yazamaz —
   `is_completed` değiştiremez, görev ekleyemez/silemez/taşıyamaz (`403`). Okumaya
   devam eder. Böylece onay sonrası uyum yüzdesi (B2) kaymaz.
5. **Rehber onaydan sonra da düzenleyebilir** — yanlış bir işareti düzeltmek onun
   yetkisidir; onay otomatik düşmez.
6. Onay geri alınırsa (`DELETE`) veli görünümü kapanır ve öğrencinin yazma yetkisi
   geri gelir.

### Öğrenciye bildirim gitmez

Öğrenci "tamamlandı" dedikten sonra onun işi biter; onay rehberin iç akışıdır.
Bu yüzden onay ucu bildirim üretmez.


## 11. Uyum yüzdesi ve dönemsel özet (B2)

### Nasıl hesaplanır

Uyum **süre** üzerinden hesaplanır (karar: kullanıcı, 25 Ağustos 2026):

```
percent = tamamlanan blokların dakikası / tüm blokların dakikası × 100
```

- Paydaya yalnızca **`counts_as_study`** bloklar girer. Dış meşguliyet (okul,
  antrenman, doktor) çalışma değildir; **denemeler çalışmadır** — B3'ün haftalık
  saat hesabıyla bilerek **aynı küme**, iki sayı birbirini tutsun diye.
- Görev sayısı değil süre sayılır: 20 dk'lık bir tekrar ile 3 saatlik bir deneme
  aynı ağırlıkta olmamalı.
- **Saatsiz programda** (ya da süresi girilmemiş bloklarda) süre yoktur; hesap
  görev sayısına düşer. Hangi yolun kullanıldığını `basis` söyler
  (`duration` / `count` / `empty`). `basis: "empty"` ise `percent` **null**'dır.

### Dönemsel özet ucu

```
GET /api/programs/compliance/?student=<id>
```

- **Rehber:** `student` zorunlu, yalnız kendi öğrencisi (aksi hâlde `404`).
  Eksikse `400`.
- **Öğrenci:** parametre yok sayılır, her zaman kendi verisi döner.
- **Veli:** çocuğu; **yalnız onaylanmış** programlar seriye girer.

```json
{
  "student": 241,
  "student_name": "Ali Yılmaz",
  "pending_approval": 1,
  "programs": [ { "id": 12, "start_date": "...", "end_date": "...", "day_count": 7,
                  "is_approved": true, ...compliance alanları } ],
  "months":   [ { "month": "2026-07", "percent": 71, "total_minutes": 1260,
                  "completed_minutes": 900, "study_hours": 21.0, "program_count": 4 } ],
  "overall":  { "percent": 76, "total_minutes": 2220, "completed_minutes": 1680,
                "study_hours": 37.0, "program_count": 7 }
}
```

**Kurallar:**

1. `programs` yalnız **bitmiş** programları içerir (eskiden yeniye). Devam eden
   hafta kısmi kalacağı için seriye girmez — anlık yüzdesi zaten program
   objesindeki `compliance` alanında var.
2. `months` ve `overall` yalnız **onaylanmış** programlardan hesaplanır. Onay,
   rehberin "gerçekten yapılmış" beyanıdır (§10); onaysız haftanın beyanı
   doğrulanmamıştır ve uzun vadeli istatistiği kirletmemelidir. Kaç haftanın onay
   beklediğini `pending_approval` söyler. Onaysız haftalar `programs` serisinde
   yine görünür (`is_approved: false`) — arayüz onları ayırarak çizmelidir.
3. Yüzdeler **dakika ağırlıklıdır**: dönemin toplam tamamlanan dakikası / toplam
   dakikası. Haftaların yüzdelerinin ortalaması **değildir** — yoksa 1 saatlik
   hafta ile 30 saatlik hafta aynı ağırlıkta sayılırdı.
4. Ay, programın **`start_date`**'ine göre seçilir (`YYYY-MM`), eskiden yeniye sıralı.
5. Hiç uygun program yoksa `percent` **null** döner (0 değil).


## 12. Çalışma istatistikleri (E2)

```
GET /api/study-stats/?student=<id>&from=YYYY-MM-DD&to=YYYY-MM-DD
```

"Şu ana kadar kaç saat çalıştım, yüzde kaç TYT / kaç AYT, hangi derse ne kadar"
sorularının cevabı. Hesap bizde, çizim (daire grafiği vb.) mobil tarafta.

**Neyi sayar:** `is_completed` işaretli **ve** `counts_as_study` bloklar — yani
gerçekten yapılan çalışma. Dış meşguliyet (okul, antrenman, doktor) sayılmaz;
denemeler sayılır. §11'deki uyum hesabıyla aynı küme.

**Roller:**
- **Öğrenci:** parametresiz kendi verisi (`student` verilse de yok sayılır).
- **Rehber:** `student` zorunlu, yalnız kendi öğrencisi (aksi hâlde `404`);
  eksikse `400`.
- **Veli:** çocuğu, ama **yalnız onaylanmış programlardaki** çalışma (B1).

```json
{
  "student": 241,
  "student_name": "Ali Yılmaz",
  "total_minutes": 1860,
  "total_hours": 31.0,
  "by_category": [
    { "category": "tyt", "minutes": 1440, "hours": 24.0, "percent": 77.4 },
    { "category": "ayt", "minutes":  420, "hours":  7.0, "percent": 22.6 }
  ],
  "by_subject": [
    { "subject": 6, "subject_label": "TYT Matematik", "category": "tyt",
      "minutes": 900, "hours": 15.0, "percent": 48.4 }
  ]
}
```

**Notlar:**

1. `by_category` ve `by_subject` **çoktan aza** sıralıdır; yüzdeler toplam
   dakikaya oranlıdır (bir ondalık).
2. Ders seçilmemiş **genel deneme** bloğu kendi kapsamına (`tyt`/`ayt`) sayılır;
   `by_subject`'e girmez (dersi yoktur). Ne dersi ne kapsamı olan blok `diger`
   kovasına düşer.
3. **Saatsiz programda süre yoktur**; o görevler toplama ve dağılıma katılmaz.
   Hiç süreli çalışma yoksa `total_minutes: 0` ve listeler boş döner.
4. `from` / `to` görevin **tarihine** (`Task.date`) göre süzer; ikisi de opsiyonel.
