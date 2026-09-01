# Rehberim — Frontend

Rehberim'in kullanıcı arayüzleri. Üç ayrı uygulama tek repo altında:

| Klasör | Kim | Teknoloji | Platform |
|--------|-----|-----------|----------|
| `rehberim_koc/` | Rehber (koç/danışman) | React + Vite | Web |
| `rehberim_ogrenci/` | Öğrenci | Flutter | Mobil |
| `rehberim_veli/` | Veli | Flutter | Mobil |

Üçü de **backend'e** (`../backend`, Django REST) `/api/` üzerinden bağlanır.
API sözleşmeleri `../backend/docs/` klasöründedir (`auth-contract.md`,
`program-contract.md`, `exam-contract.md`, `library-contract.md`, `topics-contract.md`,
`goals-calendar-contract.md`). Uç ya da alan adı değişecekse önce sözleşme güncellenir.

## Kim neyi yapıyor

| Klasör | Sahip |
|---|---|
| `rehberim_koc/` | Toprak |
| `rehberim_ogrenci/`, `rehberim_veli/` | Yunus |

Backend'in tamamı Toprak'ta; öğrenci ve veli arayüzlerini besleyen uçlar da dahil.
Başkasının klasöründe değişiklik gerekiyorsa önce haber verin.

Güncel yol haritası: [`../backend/docs/roadmap.md`](../backend/docs/roadmap.md).

## Referans belgeler

Konu ve yayınevi listeleri [`docs/`](./docs/) altında PDF olarak duruyor
(TYT/AYT konuları, Maarif müfredatı konuları, yayınevleri). **Bunları koda
gömmeyin** — üçünün de içeriği backend'de seed'li ve `/api/topics/`,
`/api/subjects/`, `/api/publishers/` uçlarından geliyor. Ayrıntı:
[`docs/README.md`](./docs/README.md).

## Önce backend'i çalıştır

Frontend'ler tek başına anlamlı değil; giriş/kayıt için backend açık olmalı.
Backend'i çalıştır (bkz. [`../backend/README.md`](../backend/README.md)):

```bash
cd ../backend && docker compose up --build
# API hazır → http://localhost:8000/api/
```

## rehberim_koc — Rehber web (React)

Node 18+ gerekir.

```bash
cd rehberim_koc
cp .env.example .env      # backend adresi hazır gelir (VITE_API_BASE_URL)
npm install
npm run dev               # → http://localhost:5173/
```

- Backend adresi `.env` içindeki `VITE_API_BASE_URL` ile ayarlanır
  (varsayılan `http://127.0.0.1:8000/api`). Koda gömülü değildir.
- Prod derleme: `npm run build` (çıktı `dist/`).

## rehberim_ogrenci / rehberim_veli — Mobil (Flutter)

Flutter SDK + bir emülatör/cihaz gerekir (Docker ile geliştirilmez).

```bash
cd rehberim_ogrenci      # veya rehberim_veli
flutter pub get
flutter run
```

- Backend adresini `lib/config/api_config.dart` platforma göre otomatik seçer:
  **Android emülatör → `10.0.2.2`**, iOS sim / masaüstü / web → `127.0.0.1`.
- Override (gerçek cihaz/prod): `flutter run --dart-define=API_BASE_URL=https://...`

## Özet akış

1. Backend'i çalıştır (`docker compose up`).
2. Kullanacağın frontend'i aç: web-rehber için `rehberim_koc`, mobil öğrenci/veli
   için ilgili Flutter uygulaması.
3. `/kayit` veya `/giris` ile hesap oluştur — istek backend'e gider.
