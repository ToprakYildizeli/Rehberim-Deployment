# Rehberim — Dağıtım

Bu repo **kod içermez.** Rehberim'i canlıya çıkarmak ve ayakta tutmak için gereken
yordamları, ortam değişkeni şablonlarını ve DNS kayıtlarını tutar.

> ⚠️ **Bu repo herkese açıktır.** Buraya hiçbir gerçek değer yazılmaz — parola,
> API anahtarı, `SECRET_KEY`, veritabanı adresi. Şablonlardaki her şey
> yer tutucudur; gerçek değerler yalnızca Railway'in ve alan adı sağlayıcının
> kendi ekranlarında durur.

Daha önce burada uygulamanın bir kopyası duruyordu; aynı kopya özel
`ToprakYildizeli/Rehberim` deposunda olduğu için kaldırıldı. Kod kopyalamak her
sürümde elle eşitleme demekti ve bir gün eski migration'la üretime çıkma riski
taşıyordu — dağıtım artık doğrudan kaynak repo'lardan yapılıyor.

## İki ürün

Rehberim 8 Ekim 2026'dan beri **iki ayrı üründür**: lise/YKS tarafı (canlıda)
ve LGS dershane tarafı (henüz dağıtılmadı). Kod, veritabanı ve dağıtım
**tamamen ayrı** — ortak kod yok, paylaşılan veritabanı yok, ayrı Railway
projeleri.

⚠️ Bir işe başlarken **önce hangi ürün olduğunu belirle.** Repo adları
birbirine çok benziyor (`Rehberim-Backend` ↔ `Rehberim-Backend-LGS`); yanlış
projenin değişkenine dokunmak en pahalı hata.

### YKS tarafı

| Parça | Kaynak repo | Nerede çalışır | Adres |
|---|---|---|---|
| Backend (Django + DRF) | `ToprakYildizeli/Rehberim-Backend` | Railway | **`api.rehberim.xyz`** ✅ |
| Rehber web (React) | `ToprakYildizeli/Rehberim-Frontend-Web` | Vercel | **`www.rehberim.xyz`** ✅ |
| Öğrenci mobil (Flutter) | `YunusCelik21/Rehberim-Frontend-Ogrenci` | mağaza / cihaz | — |
| Veli mobil (Flutter) | `YunusCelik21/Rehberim-Frontend-Veli` | mağaza / cihaz | — |
| PostgreSQL | — | Railway eklentisi | iç ağ |
| E-posta (şifre sıfırlama) | — | Resend | `noreply@rehberim.xyz` |

### LGS tarafı

| Parça | Kaynak repo | Nerede çalışır | Adres |
|---|---|---|---|
| Backend (Django + DRF) | `ToprakYildizeli/Rehberim-Backend-LGS` | Railway (**ayrı proje**) | `api-lgs.rehberim.xyz` ⏳ |
| Dershane paneli (React + TS) | `ToprakYildizeli/Rehberim-Frontend-LGS` | Vercel | `lgs.rehberim.xyz` ⏳ |
| PostgreSQL | — | Railway eklentisi (**ayrı**) | iç ağ |

LGS'de **kalıcı disk (volume) yok** — kullanıcı yüklemesi olmadığı için
gerekmiyor. YKS'de gerekiyor (profil fotoğrafları).

Mobil uygulamalar barındırma istemez; yalnızca derleme sırasında API adresini
alırlar (`--dart-define=API_BASE_URL=https://api.rehberim.xyz/api`).

## Yordamlar

| Belge | Ne zaman |
|---|---|
| [`docs/railway-backend.md`](docs/railway-backend.md) | **YKS** backend'ini ilk kez kurarken |
| [`docs/web-deploy.md`](docs/web-deploy.md) | **YKS** rehber web'ini yayına alırken |
| [`docs/lgs-railway.md`](docs/lgs-railway.md) | **LGS** backend'ini kurarken — YKS'den farkları başta yazılı |
| [`docs/lgs-web.md`](docs/lgs-web.md) | **LGS** dershane panelini yayına alırken |
| [`docs/dns.md`](docs/dns.md) | Alan adı kayıtlarını girerken |
| [`docs/email-resend.md`](docs/email-resend.md) | Şifre sıfırlama e-postalarını çalışır hâle getirirken |
| [`docs/sentry.md`](docs/sentry.md) | Hata izlemeyi bağlarken — **kişisel veri notunu oku** |
| [`docs/backup.md`](docs/backup.md) | **İlk dağıtımdan önce.** Yedeği geri yükleyemiyorsan yedeğin yok |
| [`docs/runbook.md`](docs/runbook.md) | Her dağıtımdan sonra ve bir şey bozulduğunda |

## Ortam değişkenleri

- [`env/backend.env.example`](env/backend.env.example) — YKS backend'i
- [`env/web.env.example`](env/web.env.example) — YKS rehber web'i
- [`env/lgs-backend.env.example`](env/lgs-backend.env.example) — LGS backend'i
- [`env/lgs-web.env.example`](env/lgs-web.env.example) — LGS paneli (değişken gerekmiyor)

Backend'lerin okuduğu değişkenlerin tam listesi ve açıklamaları kaynak
repo'larda: `Rehberim-Backend/Django/.env.example` ve
`Rehberim-Backend-LGS/.env.example`. Buradaki dosyalar onların **üretim için
doldurulmuş şablonu**dur; ikisi çelişirse kaynak repo kazanır.

⚠️ İki ürünün değişken adları her yerde aynı değil: CORS, YKS'de
`DJANGO_CORS_ALLOWED_ORIGINS`, LGS'de `CORS_ALLOWED_ORIGINS`.

## Dağıtım sonrası

```bash
scripts/smoke.sh https://api.rehberim.xyz            # YKS
scripts/smoke-lgs.sh https://api-lgs.rehberim.xyz    # LGS
```

Sağlık ucu, kimlik denetimi, admin arayüzü ve statik dosyaların ayakta olduğunu
tek komutla doğrular. İki betik ayrı: uçlar farklı (LGS'nin giriş ucu
`/api/auth/token/`, YKS'nin `/api/auth/login/`). Ayrıntı:
[`docs/runbook.md`](docs/runbook.md).

## Durum

> **CANLIDA (5 Eylül 2026).** Backend `api.rehberim.xyz`, rehber web
> `www.rehberim.xyz`. Kayıt ve giriş uçtan uca çalışıyor, duman testinin yedi
> kontrolü de geçiyor.

- [x] Alan adı alındı ve bağlandı — `rehberim.xyz` (5 Eylül 2026, Natro DNS)
- [x] Railway projesi kuruldu — 5 Eylül 2026, geçici adres
      `rehberim-backend-production.up.railway.app`. Duman testinin yedi
      kontrolü de geçiyor.
- [x] PostgreSQL bağlandı — tüm migration'lar uygulandı, `/healthz`
      `{"status": "ok", "database": true}` dönüyor
- [ ] **Yedekleme provası yapıldı** — `docs/backup.md`
- [x] Yönetici hesabı açıldı (`createsuperuser`) — 5 Eylül 2026
- [x] **Volume kalıcılığı kanıtlandı** — 5 Eylül 2026: `/app/media`'ya dosya
      yazıldı, yeniden dağıtım yapıldı (konteyner kimliği değişti), dosya
      yerinde duruyordu.
- [ ] Sentry bağlandı ve test olayı düştü
- [ ] Resend alan adı doğrulaması tamam, gerçek adrese test maili gitti
- [x] Rehber web yayında — `rehberim-frontend-web.vercel.app` (Vercel),
      5 Eylül 2026. CORS açıldı, kayıt zinciri uçtan uca doğrulandı.
- [ ] SPA yönlendirmesi denendi (`/panel`'de F5, `/sifre-sifirla/abc/def`)
- [ ] **Kök `rehberim.xyz` açılmıyor** — yalnız `www` çalışıyor. Natro'daki A
      kaydı Vercel'in IP'sine (`76.76.21.21`) çevrilmeli; eski park IP'si
      (`85.159.66.93`) kalmış olabilir.
- [ ] HSTS açıldı (HTTPS doğrulandıktan **sonra**)

### LGS tarafı

> **HENÜZ CANLIDA DEĞİL.** Kod tarafı 10 Ekim 2026'da üretime hazırlandı
> (Dockerfile, HTTPS sertleştirmesi, günlükleme, CI, şifre sıfırlama, paket
> zorlaması); Railway/Vercel kurulumu yapılmadı.

- [ ] Railway projesi açıldı (**YKS'den ayrı**) — [`docs/lgs-railway.md`](docs/lgs-railway.md)
- [ ] PostgreSQL bağlandı (**ayrı eklenti**), migration'lar uygulandı
- [ ] `api-lgs.rehberim.xyz` bağlandı, sertifika çıktı
- [ ] Yönetici hesabı açıldı (`createsuperuser`) — paket yönetimi admin'den
- [ ] Dershane paneli yayında — `lgs.rehberim.xyz`, [`docs/lgs-web.md`](docs/lgs-web.md)
- [ ] SPA yönlendirmesi denendi (`/denemeler`'de F5, `/sifre-sifirla/abc/def`)
- [ ] E-posta bağlandı (**port 2587**) — olmadan şifre sıfırlama çalışmaz
- [ ] Yedekleme provası yapıldı — [`docs/backup.md`](docs/backup.md)
- [ ] `scripts/smoke-lgs.sh` tüm kontrolleri geçiyor
- [ ] HSTS açıldı (HTTPS doğrulandıktan **sonra**)
- [ ] Sentry — **LGS kodunda entegrasyon yok**, önce yazılması gerekir
