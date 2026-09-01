# Rehberim

Öğrenci, rehber (koç/danışman) ve veliyi tek platformda buluşturan bir eğitim takip
uygulamasıdır. Öğrenci günlük programını, kitaplığını, deneme sonuçlarını ve konu
kazanımlarını takip eder; rehber öğrencilerine program hazırlar, kazanım girer ve
gidişatı izler.

Detaylı ürün kapsamı için: [`Rehberim MVP.pdf`](./Rehberim%20MVP.pdf).

## Teknoloji Yığını

- **Backend:** Django 6.0 + Django REST Framework (JWT auth: `simplejwt`, CORS: `django-cors-headers`)
- **Dil:** Python 3.14
- **Bağımlılık yönetimi:** Pipenv (`Django/Pipfile`)
- **Veritabanı:** SQLite (geliştirme) — üretimde PostgreSQL hedefleniyor
- **Web frontend (rehber):** React — `../frontend/rehberim_koc`, API üzerinden bağlanır
- **Mobil (öğrenci + veli):** Flutter — `../frontend/rehberim_ogrenci`, `../frontend/rehberim_veli`

> Web = **sadece rehber**, Mobil = **öğrenci + veli**. İki frontend de backend'e
> REST API (`/api/`) ile bağlanır. Backend'deki Django template login/register'ı
> geliştirme/admin için tutulan bir ara çözümdür.

## Proje Yapısı

```
Rehberim/
├── docker-compose.yml       # geliştirici ortamı (docker compose up)
├── Django/                  # Django kökü (manage.py burada)
│   ├── Dockerfile           # backend imajı (Python 3.14 + pipenv)
│   ├── manage.py
│   ├── Pipfile
│   ├── Django/              # proje ayar paketi (settings, urls, wsgi, asgi)
│   ├── accounts/            # KİMLİK & AUTH app'i
│   │   ├── models.py        # User, Counselor, Student, Parent (+ davet kodları)
│   │   ├── serializers.py   # API veri şekilleri + kayıt mantığı
│   │   ├── api_views.py     # API endpoint'leri (login/register/me/connect...)
│   │   ├── api_urls.py      # /api/ altındaki rotalar
│   │   ├── permissions.py   # IsCounselor / IsStudent / IsParent
│   │   ├── views.py, forms.py, urls.py   # web (template) auth — rehber
│   │   └── templates/
│   └── Rehberim/            # DOMAIN app'i
│       ├── models.py        # program/görev, deneme, hedef, takvim, kitaplık, konular
│       ├── api_views.py, serializers.py, api_urls.py, permissions.py
│       ├── management/commands/seed_mockdata.py   # örnek veri
│       ├── migrations/      # konu ve yayınevi seed'leri de burada (data migration)
│       └── templates/rehber/
├── docs/
│   ├── roadmap.md           # YOL HARİTASI — hoca geri bildirimine göre
│   ├── auth-contract.md     # kimlik sözleşmesi (v1.1)
│   ├── program-contract.md  # program, görev, şablon, rutin
│   ├── exam-contract.md     # denemeler ve net hesabı
│   ├── goals-calendar-contract.md
│   ├── library-contract.md
│   └── topics-contract.md
├── Rehberim MVP.pdf         # ürün planı
├── README.md
└── CLAUDE.md
```

## Çalıştırma

### Seçenek A — Docker (önerilen, tek komut)

Python/pipenv kurmana gerek yok. Sadece Docker Desktop kurulu olsun.

```bash
docker compose up --build
```

Bu komut bağımlılıkları kurar, migrasyonları uygular ve sunucuyu başlatır.
Kodu düzenledikçe konteyner canlı yeniden yükler (volume mount). Durdurmak: `Ctrl+C`.

> **Port çakışması?** `8000` başka bir uygulamada doluysa `docker compose up`
> "port is already allocated" verir. O uygulamayı durdur ya da geçici farklı port:
> `docker compose run --service-ports -p 8010:8000 backend`.

Yönetici kullanıcı (admin paneli için, opsiyonel):

```bash
docker compose exec backend python manage.py createsuperuser
```

### Seçenek B — Yerel (Pipenv)

```bash
cd Django
pipenv install
pipenv shell
python manage.py migrate
python manage.py createsuperuser   # opsiyonel (admin paneli)
python manage.py runserver
```

### Adresler

- API kökü: <http://127.0.0.1:8000/api/>
- Rehber web (template): <http://127.0.0.1:8000/accounts/login/>
- Admin paneli: <http://127.0.0.1:8000/admin/>

> Frontend (React/Flutter) bu backend'e `/api/` üzerinden bağlanır. Backend'i önce
> çalıştır, sonra frontend'i aç. CORS izinli dev origin'leri: `localhost:5173`
> (React), `localhost:3000`. Frontend kurulumu için [`../frontend/README.md`](../frontend/README.md).

## Uygulamalar & Veri Modeli

Kimlik/rol modelleri `accounts`, domain modelleri `Rehberim` app'inde. Bağımlılık
tek yönlü: `Rehberim → accounts`.

**`accounts` (kimlik):**

| Model | Açıklama |
|-------|----------|
| `User` | `AbstractUser` tabanlı özel kullanıcı; `is_student` / `is_counselor` / `is_parent` bayrakları. `AUTH_USER_MODEL = 'accounts.User'` |
| `Counselor` | Rehber profili (User 1-1); `invite_code` — benzersiz ve **değişmez**; öğrenci ve veli bununla bağlanır |
| `Student` | Öğrenci profili; sınıf düzeyi, alan (say/EA/söz). `connect_code` artık kullanılmıyor (veli id + hoca koduyla bağlanır) |
| `Parent` | Veli profili; öğrencilerle M2M |

**`Rehberim` (domain):**

| Model | Açıklama |
|-------|----------|
| `Subject` | Ders; TYT / AYT / Okul kategorileri. `question_count` = sınavdaki soru sayısı |
| `ExamResult` + `SubjectNet` | Deneme sonucu ve ders bazlı sonuçlar. Öğrenci **doğru/yanlış** girer; net ve boş sunucuda türetilir |
| `WeeklyProgram` + `Task` | Program ve içindeki bloklar. Uzunluk esnek (`day_count`, varsayılan 7); bloklar `study` / `external` (çalışma saatine sayılmaz) / `exam` (genel TYT/AYT olabilir) |
| `TaskType` | Çalışma metodu (Konu Çalışması, Test, Deneme, Video İzleme) |
| `ProgramTemplate` + `TemplateTask` | Tekrar kullanılabilir şablon program. Öğrenciye bağlanıp `auto_apply` açılırsa **rutin** olur |
| `Goal` | Hedefler (net, kitap bitirme, konu bitirme, kitap okuma) |
| `CalendarEvent` | Rehberin takvimi: görüşme, veli toplantısı, sınav tarihi |
| `Publisher` + `Book` + `BookTopic` | Kitaplık; ders kitaplarında konular otomatik dolar |
| `Topic` + `TopicProgress` | Konu kataloğu ve öğrenci bazlı ilerleme (1–5 seviye) |

Öğrencinin göreceği dersler sınıf düzeyine göre belirlenir (12. sınıf ve mezunlar
TYT/AYT dersleri, alt sınıflar okul derslerini görür — bkz. `Student.available_subjects`).

### Deneme netleri

Net **girilmez, türetilir.** Öğrenci ders başına doğru ve yanlış sayısını gönderir:

```
net  = doğru - yanlış / 4
boş  = soru sayısı - doğru - yanlış
```

`net`, `blank` ve `question_count` salt-okunurdur; `doğru + yanlış` dersin soru
sayısını aşarsa `400` döner. Hepsi yanlışsa net doğal olarak negatif çıkar.
Sözleşme: [`docs/exam-contract.md`](./docs/exam-contract.md).

### Rutin (tekrarlayan program)

Rutin ayrı bir model **değil**: bir `ProgramTemplate`'e öğrenci bağlanıp
`auto_apply` açılırsa o şablon artık o öğrencinin rutinidir. Öğrenciye yeni bir
hafta açıldığında rutindeki görevler o haftaya kendiliğinden materyalize edilir.
Rutini **hem rehber hem öğrenci** kurabilir; öğrenci yalnızca kendi rutinini
görür ve kurar. Ayrıntı: [`docs/program-contract.md`](./docs/program-contract.md).

## API

Tüm uçlar `/api/` altında, JWT ile korunur (access + refresh).

### Kimlik

| Endpoint | Açıklama |
|----------|----------|
| `POST /api/auth/login/` | access + refresh + kullanıcı/rol döner |
| `POST /api/auth/refresh/` | yeni access token |
| `POST /api/auth/logout/` | refresh token'ı blacklist'e alır |
| `GET /api/auth/me/` | giriş yapan kullanıcı + rol + profil |
| `PATCH /api/auth/me/` | kendi ad/soyad/e-postasını günceller |
| `POST /api/auth/register/{counselor,student,parent}/` | rol bazlı self-register |
| `POST /api/students/connect-counselor/` | öğrenci → rehbere davet koduyla bağlanır |
| `POST /api/parents/connect-student/` | veli → öğrencinin id'si + rehberin davet koduyla bağlanır |

Öğrenci ve veli mobilden kendileri kaydolur, sonra davet kodlarıyla bağlanır.
Rehber web'den kaydolur. Web girişi yalnızca rehberlere açıktır.

### Domain

| Endpoint | Açıklama |
|----------|----------|
| `/api/programs/` · `/api/programs/current/` · `/api/programs/{id}/tasks/` · `/api/tasks/{id}/` | Haftalık program ve görevler |
| `/api/program-templates/` · `/api/programs/assign/` | Şablon programlar, rutin ve öğrenciye atama |
| `/api/exams/` | Denemeler + ders bazlı doğru/yanlış |
| `/api/goals/` | Hedefler |
| `/api/calendar/` | Rehberin takvimi (görüşme, sınav) |
| `/api/books/` · `/api/publishers/` · `/api/book-topics/` | Kitaplık |
| `/api/topics/` · `/api/topic-progress/` | Konu kataloğu ve 1–5 seviye ilerleme |
| `/api/subjects/` · `/api/task-types/` · `/api/students/` | Katalog ve öğrenci listesi |

### Sözleşmeler

Endpoint/alan adı değiştirmeden önce ilgili sözleşmeye bakın ve iki frontend'e de
haber verin:

| Belge | Kapsam |
|---|---|
| [`docs/auth-contract.md`](./docs/auth-contract.md) | Kimlik (v2.0) |
| [`docs/program-contract.md`](./docs/program-contract.md) | Program, görev, şablon, **rutin** |
| [`docs/exam-contract.md`](./docs/exam-contract.md) | Denemeler ve net hesabı |
| [`docs/goals-calendar-contract.md`](./docs/goals-calendar-contract.md) | Hedefler ve takvim |
| [`docs/library-contract.md`](./docs/library-contract.md) | Kitaplık |
| [`docs/topics-contract.md`](./docs/topics-contract.md) | Konular ve konu ilerlemesi |

## Test ve örnek veri

```bash
cd Django
python manage.py test                     # 178 test
python manage.py seed_mockdata            # demo seti (mock_* kullanıcıları)
python manage.py seed_mockdata --weeks 30 # daha derin geçmiş
python manage.py seed_mockdata --bulk     # ölçekli rastgele veri
python manage.py seed_mockdata --clear
```

Demo seti **20 haftalık** (varsayılan) program geçmişi üretir: haftalar birbirinin
kopyası değildir — çalışma hacmi ve tamamlanma oranı zamanla artar, deneme netleri
yükselen bir eğilim izler, konu ilerlemesi müfredat sırasında baştan sona azalır.
Grafiklerin bir şey göstermesi için gereken derinlik budur. Bloklar üç türü de
kapsar (çalışma / okul-antrenman gibi dış meşguliyet / genel TYT-AYT denemesi) ve
süreleri 20 dk ile 5 saat arasında değişir.

Seed komutu **yalnızca `mock_` önekli veriye dokunur**, idempotenttir. Şifre hepsinde
aynıdır (bkz. komutun başındaki `MOCK_PASSWORD`).

> **Dikkat:** migration `0018` `correct`/`wrong` alanlarını `default=0` ile ekler ve
> geriye dönük doldurmaz. `migrate` sonrası `seed_mockdata` çalıştırılmazsa eski
> deneme kayıtlarının netleri ilk kaydetmede sıfırlanır.

## Yol Haritası

Güncel plan ayrı bir belgede: **[`docs/roadmap.md`](./docs/roadmap.md)** — hocanın
22 Ağustos 2026 geri bildirimine göre yazıldı, rehber web + backend kapsamını
fazlara böler ve kimin neyi yaptığını netleştirir.

**Bitmiş:** kimlik/rol + JWT API auth · programlar ve görevler · şablon programlar
ve **rutin** · denemeler (doğru/yanlış girişi) · hedefler · takvim · kitaplık ·
konu kataloğu ve 1–5 seviye konu ilerlemesi · nesne bazlı yetkilendirme ·
profil düzenleme.

**Yeni bitti:** ders programında **esnek pencere** (`day_count`, örtüşme yasağı) ve
**yeni blok türleri** (`kind`: çalışma / dış meşguliyet / deneme, genel TYT-AYT
denemesi) — backend ve rehber web arayüzü birlikte.

**Sırada (özet):** esnek süre ve süre hafızası · iki tahta görünümü · haftalık
**onay akışı** ve uyum yüzdesi · başarımlar · panel ve takvim düzeltmeleri ·
Ayarlar. Ayrıntı ve bağımlılıklar için yol haritasına bakın.

**Kapsam dışı:** deneme foto/OCR aktarımı, üretim sertleştirmesi (şimdilik).
