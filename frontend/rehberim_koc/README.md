# rehberim_koc — Rehber web arayüzü

Rehberin (koç/danışman) kullandığı web uygulaması. React + Vite. Backend'e
`/api/` üzerinden bağlanır; tek başına anlamlı değildir, önce backend çalışmalıdır.

> Web **yalnızca rehber** içindir. Öğrenci ve veli mobil uygulamalarını kullanır.

## Çalıştırma

Node 18+ gerekir.

```bash
cp .env.example .env      # VITE_API_BASE_URL hazır gelir
npm install
npm run dev               # → http://localhost:5173/
npm run build             # prod derleme → dist/
```

Backend adresi `.env` içindeki `VITE_API_BASE_URL` ile ayarlanır (varsayılan
`http://127.0.0.1:8000/api`). **Koda gömülü adres yok.**

Backend'in CORS listesinde `localhost:5173` ve `localhost:3000` var; başka bir
portta çalıştırırsan backend `settings.py`'daki `CORS_ALLOWED_ORIGINS`'e eklemen
gerekir.

## Ekranlar

| Rota | Ne yapar |
|---|---|
| `/panel` | Bekleyen aksiyonlar, kırmızı alarmlar, aktivite akışı — hepsi gerçek veriden türetilir |
| `/ogrenciler` | Öğrenci listesi + rehberin **davet kodu** (öğrenci bununla bağlanır) |
| `/ogrenciler/:id` | Öğrenci detayı — Kitaplar · Denemeler · Ders Programı (geçmiş dahil) · Konu Takibi |
| `/ders-programi` | Haftalık program tahtası: sürükle-bırak bloklar, şablon kaydetme, öğrenciye atama, **rutin** |
| `/takvim` | Görüşme, veli toplantısı ve sınav takvimi |
| `/ayarlar` | Profil düzenleme, tema, çıkış |

## Yapı

```
src/
├── api/            # backend uçlarına karşılık gelen modüller (client.js = axios + JWT)
├── components/     # ui/ (tasarım sistemi), layout/, dashboard/
├── context/        # AuthContext (oturum), ThemeContext
├── pages/          # yukarıdaki ekranlar
└── mocks/data.js   # tahtanın sabitleri (SUBJECTS, DAYS, HOURS) — mock veri DEĞİL
```

**`api/client.js`** her isteğe JWT ekler ve 401'de refresh token ile bir kez yeniden
dener; refresh de geçersizse oturumu kapatıp `/giris`'e atar.

## Kurallar

- **Katalog verisi backend'den gelir.** Ders, konu, çalışma metodu, yayınevi ve
  kitap seçimleri serbest metin değil, ilgili uçtan beslenen listelerdir
  (`/api/subjects/`, `/api/topics/?subject=`, `/api/task-types/`, `/api/publishers/`,
  `/api/books/?student=`). Konu ve yayınevi PDF'leri `../docs/` altındadır ama
  referanstır — koda gömülmez.
- **Ekranlar birbirine bağlıdır.** Takvimde açılan bir toplantı, Öğrenciler
  kartında "sonraki toplantı" olarak görünmelidir.
- Uç ya da alan adı değişecekse önce backend'deki sözleşme (`../../backend/docs/`)
  güncellenir.

Yol haritası: [`../../backend/docs/roadmap.md`](../../backend/docs/roadmap.md).
