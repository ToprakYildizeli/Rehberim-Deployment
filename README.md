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

## Parçalar

| Parça | Kaynak repo | Nerede çalışır | Adres |
|---|---|---|---|
| Backend (Django + DRF) | `ToprakYildizeli/Rehberim-Backend` | Railway | `api.rehberim.xyz` |
| Rehber web (React) | `ToprakYildizeli/Rehberim-Frontend-Web` | statik barındırma | `rehberim.xyz` |
| Öğrenci mobil (Flutter) | `YunusCelik21/Rehberim-Frontend-Ogrenci` | mağaza / cihaz | — |
| Veli mobil (Flutter) | `YunusCelik21/Rehberim-Frontend-Veli` | mağaza / cihaz | — |
| PostgreSQL | — | Railway eklentisi | iç ağ |
| E-posta (şifre sıfırlama) | — | Resend | `noreply@rehberim.xyz` |

Mobil uygulamalar barındırma istemez; yalnızca derleme sırasında API adresini
alırlar (`--dart-define=API_BASE_URL=https://api.rehberim.xyz/api`).

## Yordamlar

| Belge | Ne zaman |
|---|---|
| [`docs/railway-backend.md`](docs/railway-backend.md) | Backend'i ilk kez kurarken |
| [`docs/web-deploy.md`](docs/web-deploy.md) | Rehber web'ini yayına alırken |
| [`docs/dns.md`](docs/dns.md) | Alan adı kayıtlarını girerken |
| [`docs/email-resend.md`](docs/email-resend.md) | Şifre sıfırlama e-postalarını çalışır hâle getirirken |
| [`docs/sentry.md`](docs/sentry.md) | Hata izlemeyi bağlarken — **kişisel veri notunu oku** |
| [`docs/backup.md`](docs/backup.md) | **İlk dağıtımdan önce.** Yedeği geri yükleyemiyorsan yedeğin yok |
| [`docs/runbook.md`](docs/runbook.md) | Her dağıtımdan sonra ve bir şey bozulduğunda |

## Ortam değişkenleri

- [`env/backend.env.example`](env/backend.env.example) — Railway'e girilecekler
- [`env/web.env.example`](env/web.env.example) — statik barındırmaya girilecekler

Backend'in okuduğu değişkenlerin tam listesi ve açıklamaları kaynak repo'da:
`Rehberim-Backend/Django/.env.example`. Buradaki dosya onun **üretim için
doldurulmuş şablonu**dur; ikisi çelişirse kaynak repo kazanır.

## Dağıtım sonrası

```bash
scripts/smoke.sh https://api.rehberim.xyz
```

Sağlık ucu, kimlik denetimi, admin arayüzü ve statik dosyaların ayakta olduğunu
tek komutla doğrular. Ayrıntı: [`docs/runbook.md`](docs/runbook.md).

## Durum

- [x] Alan adı alındı — `rehberim.xyz` (5 Eylül 2026)
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
- [ ] Rehber web yayında, SPA yönlendirmesi çalışıyor
- [ ] HSTS açıldı (HTTPS doğrulandıktan **sonra**)
