# Runbook — dağıtım sonrası ve arıza anı

## Her dağıtımdan sonra

```bash
scripts/smoke.sh https://api.rehberim.xyz
```

Sonra elle iki şey:

- Rehber web'inde giriş yap
- `/panel`'de F5'e bas (SPA yönlendirmesi)

## Belirtiden sebebe

| Belirti | Muhtemel sebep | Bakılacak yer |
|---|---|---|
| Konteyner açılmıyor, "DJANGO_SECRET_KEY tanımlı değil" | Değişken girilmemiş | Railway → Variables |
| Konteyner açılmıyor, "DATABASE_URL tanımlı değil" | PostgreSQL referansı bağlanmamış | Railway → Variables |
| `/healthz` 503 | Uygulama ayakta, veritabanına ulaşamıyor | PostgreSQL eklentisi, iç ağ adresi |
| Tüm istekler 400 "DisallowedHost" | `DJANGO_ALLOWED_HOSTS` eksik/yanlış | Variables |
| Arayüz açılıyor ama hiçbir veri gelmiyor | CORS | `DJANGO_CORS_ALLOWED_ORIGINS` |
| Admin arayüzü stilsiz | `collectstatic` çalışmamış | Dağıtım günlüğü, imaj derlemesi |
| Profil fotoğrafları dağıtımdan sonra kayboldu | Volume bağlı değil | Railway → volume, `/app/media` |
| Şifre sıfırlama maili gelmiyor | SMTP tanımsız ya da DNS eksik | `DJANGO_EMAIL_HOST`, [`email-resend.md`](email-resend.md) |
| Mail geliyor ama gereksiz postada | SPF/DKIM/DMARC eksik | [`dns.md`](dns.md) |
| Sıfırlama bağlantısı 404 | SPA yönlendirmesi yok | [`web-deploy.md`](web-deploy.md) |
| Sıfırlama isteği 429 | Hız sınırı (IP başına 5/saat) | Beklenen davranış, bekle |
| Admin formu "CSRF doğrulaması başarısız" | `DJANGO_CSRF_TRUSTED_ORIGINS` eksik | Variables |

## Geri alma

Railway önceki dağıtıma dönmeyi destekliyor. **Ama migration geri alınmaz:**
`0030` gibi veri taşıyan bir migration uygulandıktan sonra eski koda dönmek
şemayı uyumsuz bırakabilir. Kod geri alınmadan önce migration'ın ne yaptığına
bak; gerekiyorsa yedekten dönmek daha güvenli → [`backup.md`](backup.md).

## Henüz yok

Dağıtımdan önce kapatılması istenenlerin tam listesi kaynak repo'da:
`Rehberim-Backend/docs/deployment.md` → "Dağıtımdan önce kapatılması gereken
ürün eksikleri". Özet:

- Giriş, kayıt ve davet kodu uçlarında **hız sınırı yok** (yalnız şifre
  sıfırlamada var)
- **Sayfalama yok** — listeler tabloyu bütün döndürüyor
- **Hata izleme yok** (Sentry vb.); bir şey patlarsa kimsenin haberi olmuyor
- **KVKK** belgeleri yok — reşit olmayan öğrenci verisi işleniyor
