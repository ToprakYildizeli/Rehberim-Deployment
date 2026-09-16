# DNS kayıtları — `rehberim.xyz`

Hepsi alan adı sağlayıcının DNS panelinde tanımlanır. Gerçek hedef değerleri
Railway, statik barındırma ve Resend kendi ekranlarında verir; **buraya
yazılmaz** (bu repo herkese açık).

## Kayıtlar

| Ad | Tür | Değer | Nereden gelir | Ne için |
|---|---|---|---|---|
| `api` | CNAME | Railway'in verdiği hedef | Railway → alan adı ekranı | Backend API |
| `@` | A / ALIAS | Barındırmanın verdiği | Vercel / Cloudflare Pages | Rehber web |
| `www` | CNAME | Barındırmanın verdiği | aynı | Rehber web |
| `send` | CNAME | Resend'in verdiği | Resend | E-posta yetkilendirme (SPF) |
| `rsend` | CNAME | Resend'in verdiği | Resend | aynı (bölge sunucusu) |
| `resend._domainkey` | TXT | Resend'in verdiği `p=...` | Resend | E-posta imzası (DKIM) |
| `_dmarc` | TXT | `v=DMARC1; p=none;` | elle | E-posta raporlama (DMARC) |

⚠️ **SPF artık `@` üzerinde TXT değil.** Resend SPF'i `send`/`rsend` alt
alanlarına CNAME ile bağlıyor; kök alan adına `v=spf1 ...` yazmak gerekmiyor
(16 Eylül 2026'da böyle kuruldu ve doğrulandı). Eski belge `@` TXT'si
anlatıyordu, o yol artık geçerli değil.

## Sıra önemli

1. **Önce `api` kaydı** — Railway sertifikayı ancak DNS çözüldükten sonra çıkarır.
2. **Sonra e-posta kayıtları** — Resend alan adını doğrulamadan mail göndermez.
3. **En son web** — API ayakta olmadan arayüzü yayına almanın anlamı yok.

## DMARC hakkında

`p=none` ile başla: e-posta **reddedilmez**, yalnız raporlanır. Birkaç gün
raporlara bakıp her şeyin imzalandığını gördükten sonra `p=quarantine`e
geçebilirsin.

`p=reject` ile başlamak, bir yapılandırma hatasında **şifre sıfırlama
e-postalarının sessizce yok olması** demektir. Bu üründe şifre sıfırlama tek
kurtarma yolu, o riski alma.

## `.xyz` notu

`.xyz` uzantısının e-posta itibarı `.com`'a göre zayıf. Yukarıdaki üç kaydın
(SPF + DKIM + DMARC) **üçü birden** doğru olmadan Gmail ve Outlook postaları
gereksiz klasörüne atabilir. Bu yüzden bunlar isteğe bağlı değil, zorunlu.

## Doğrulama

```bash
dig +short api.rehberim.xyz
dig +short TXT resend._domainkey.rehberim.xyz   # DKIM (p=... ile başlar)
dig +short CNAME send.rehberim.xyz              # SPF zincirinin girişi
dig +short TXT _dmarc.rehberim.xyz              # DMARC
dig +short TXT send.forge.rmta.net              # zincir çözülüyor mu (v=spf1 ...)
```

DKIM değeri 255 karakterden uzun olduğu için DNS onu parçalara böler;
`dig` çıktısında tırnaklar arasında görünmesi normaldir. Doğruluğunu
kontrol ederken parçaları birleştirip Resend'in verdiği değerle
**karakter karakter** karşılaştır — panelde kaçan tek bir boşluk
doğrulamayı sessizce düşürür.

DNS yayılması 5 dakika ile birkaç saat arasında sürebilir; hemen görünmemesi
hata demek değildir.
