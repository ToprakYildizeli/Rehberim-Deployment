# Rehber web'ini yayına alma

Kaynak: `ToprakYildizeli/Rehberim-Frontend-Web` · Hedef: `rehberim.xyz`

Uygulama saf statik dosya (React + Vite). Sunucu istemez; Vercel, Cloudflare
Pages ya da Netlify'ın ücretsiz katı fazlasıyla yeter. Backend'i Railway'de
tutup web'i buraya almak Railway kaynağını da boşa harcamamış olur.

## Derleme ayarları

| Ayar | Değer |
|---|---|
| Derleme komutu | `npm run build` |
| Çıktı dizini | `dist` |
| Kurulum | `npm ci` |
| Node | 22 |

## Ortam değişkeni

```
VITE_API_BASE_URL=https://api.rehberim.xyz/api
```

⚠️ **Vite değişkenleri derleme anında pakete gömülür.** Değiştirdiğinde yeniden
derlemek gerekir; barındırmanın panelinden değeri değiştirip "kaydet" demek
yetmez. Aynı sebeple buraya gizli hiçbir şey yazılmaz — paketi indiren herkes
görür.

Sondaki `/api` **var**, sondaki eğik çizgi **yok**. İkisi de önemli.

## SPA yönlendirmesi — atlanırsa yenileme 404 verir

Uygulama istemci tarafında yönlendiriyor. Kullanıcı `/panel` sayfasındayken F5'e
bastığında barındırma diskte `/panel` diye bir dosya arar, bulamaz, 404 döner.
Bütün yolların `index.html`e düşmesi gerekir.

- **Vercel / Netlify:** çoğu şablonda hazır gelir, gelmiyorsa yeniden yazma
  (rewrite) kuralı: `/*` → `/index.html` (200)
- **Cloudflare Pages:** repo köküne `_redirects` dosyası — `/*  /index.html  200`

Şifre sıfırlama sayfası (`/sifre-sifirla/<uid>/<token>`) **doğrudan e-postadaki
bağlantıyla açılıyor**, yani bu kural olmadan şifre sıfırlama hiç çalışmaz.
Test ederken özellikle bu adrese doğrudan git.

## Alan adı

`rehberim.xyz` ve `www.rehberim.xyz` → [`dns.md`](dns.md)

Alan adı bağlandıktan sonra backend'e dön ve CORS'u güncelle:

```
DJANGO_CORS_ALLOWED_ORIGINS=https://rehberim.xyz,https://www.rehberim.xyz
```

Bu yapılmazsa arayüz açılır ama **her API çağrısı tarayıcı tarafından
engellenir** — konsol dışında hiçbir yerde görünmeyen bir arıza.

## Doğrulama

1. `https://rehberim.xyz` açılıyor
2. Giriş yapılıyor (API'ye ulaşıyor demektir)
3. `/panel`'e git, **F5'e bas** — 404 gelmiyor
4. `https://rehberim.xyz/sifre-sifirla/abc/def` adresine doğrudan git —
   sayfa açılmalı (token geçersiz diyecek, önemli değil; sayfanın açılması yeter)
