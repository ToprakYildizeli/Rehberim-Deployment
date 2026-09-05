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
| `@` | TXT | `v=spf1 include:...` | Resend | E-posta yetkilendirme (SPF) |
| `resend._domainkey` | TXT/CNAME | Resend'in verdiği | Resend | E-posta imzası (DKIM) |
| `_dmarc` | TXT | `v=DMARC1; p=none; rua=mailto:...` | elle | E-posta raporlama (DMARC) |

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
dig +short TXT rehberim.xyz          # SPF görünmeli
dig +short TXT _dmarc.rehberim.xyz   # DMARC görünmeli
```

DNS yayılması 5 dakika ile birkaç saat arasında sürebilir; hemen görünmemesi
hata demek değildir.
