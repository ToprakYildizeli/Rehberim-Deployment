# LGS dershane panelini yayına alma

Kaynak: `ToprakYildizeli/Rehberim-Frontend-LGS` · Hedef: `lgs.rehberim.xyz`

Uygulama saf statik dosya (React + Vite + TS). Sunucu istemez.

**Durum: yayında (14 Ekim 2026).** Vercel projesi `rehberim-frontend-lgs`,
`main` dalından dağıtılıyor; yedek adres `rehberim-frontend-lgs.vercel.app`.
`lgs.rehberim.xyz` bağlı ve sertifikası geçerli.

> **Neden `lgs.rehberim.xyz`, neden `rehberim.xyz/lgs` değil.**
> Yol haritasının Faz 8 planı path tabanlıydı: `rehberim.xyz/lgs` ve
> `rehberim.xyz/yks`. Bu, **canlıdaki** YKS web'ini `www.rehberim.xyz`'den bir
> alt yola taşımayı gerektiriyor — çalışan bir ürünü, henüz dağıtılmamış bir
> ürün için riske atmak. Ayrı alt alan adı aynı sonucu veriyor ve YKS tarafına
> hiç dokunmuyor (karar: 10 Ekim 2026). Ortak karşılama sayfası
> (`Rehberim-Gateway`) gerekirse sonra, kök alan adı üzerinde açılabilir.

## Derleme ayarları

| Ayar | Değer |
|---|---|
| Derleme komutu | `npm run build` |
| Çıktı dizini | `dist` |
| Kurulum | `npm ci` |
| Node | 22 |
| Kök dizin | repo kökü (boş bırak) |

`npm run build` önce `tsc -b` çalıştırıyor; tür hatası varsa derleme durur.

## Ortam değişkeni — **gerekmiyor**

API adresi **kaynakta** duruyor: `src/api/client.ts`. Sayfa `localhost`ta
açıldıysa `http://127.0.0.1:8100/api`, değilse `https://api-lgs.rehberim.xyz/api`.

Gerekçe YKS tarafında ölçülerek bulundu (5 Eylül 2026): **Vercel repo'daki
`.env*` dosyalarını derlemeye dahil etmiyor** ve paneli `VITE_` önekli
değişkeni "tarayıcıya açılır" uyarısıyla kaydettirmiyor — oysa önek zorunlu,
Vite yalnız onunla başlayanları pakete gömüyor.

`VITE_API_BASE_URL` tanımlanabiliyorsa yine o kazanır. **Adres değişirse
`src/api/client.ts` güncellenmeli.**

## SPA yönlendirmesi

Repo kökündeki `vercel.json` kuralı tanımlıyor (`/(.*)` → `/index.html`).
Vercel dışında bir yere alınırsa elle kurulmalı:

- **Netlify:** rewrite `/*` → `/index.html` (200)
- **Cloudflare Pages:** repo köküne `_redirects` → `/*  /index.html  200`

⚠️ Bu kural olmadan `/denemeler` adresinde F5 **404** verir ve
`/sifre-sifirla/<uid>/<token>` bağlantısı hiç açılmaz — yani **şifre sıfırlama
çalışmaz.** Test ederken özellikle bu adrese doğrudan git.

## Alan adı

`lgs.rehberim.xyz` → [`dns.md`](dns.md)

Vercel → proje → **Domains → Add** → alan adını yaz, *Connect to an
environment: Production* seçili kalsın. Verdiği CNAME hedefini DNS panelinde
`lgs` adıyla tanımla. Railway'in aksine Vercel **ayrı bir doğrulama TXT'si
istemiyor**; CNAME yayılınca sertifika kendiliğinden çıkıyor.

⚠️ Depo özel olduğu için Vercel'in GitHub uygulamasının bu depoya erişimi
olmalı — Railway tarafında bu yüzden yarım saat kaybedildi (bkz.
[`lgs-railway.md`](lgs-railway.md) §1). Vercel'de depo listede görünmüyorsa:
GitHub → Settings → Applications → Vercel → Configure.

Bağlandıktan sonra **backend'e dön** ve iki değişkeni güncelle:

```
CORS_ALLOWED_ORIGINS=https://lgs.rehberim.xyz
DJANGO_PASSWORD_RESET_URL=https://lgs.rehberim.xyz/sifre-sifirla/{uid}/{token}
```

⚠️ Değişkenin adı **`CORS_ALLOWED_ORIGINS`** — YKS'de
`DJANGO_CORS_ALLOWED_ORIGINS`. İki ayrı kod tabanı, iki ayrı ad.

CORS yapılmazsa arayüz açılır ama **her API çağrısı tarayıcı tarafından
engellenir** — konsol dışında hiçbir yerde görünmeyen bir arıza.
`DJANGO_PASSWORD_RESET_URL` yanlış kalırsa postadaki bağlantı `localhost:5183`
adresini gösterir.

## Doğrulama

1. `https://lgs.rehberim.xyz` açılıyor, giriş ekranı geliyor.
2. Kayıt → giriş zinciri çalışıyor (yeni bir hesap açılıyor).
3. `/denemeler` sayfasında **F5** — 404 vermemeli.
4. `https://lgs.rehberim.xyz/sifre-sifirla/abc/def` adresine doğrudan git —
   sayfa açılmalı (bağlantı geçersiz diyecek, önemli olan 404 vermemesi).
5. Şifremi unuttum → gerçek bir adrese posta gidiyor mu. **Backend'de
   `DJANGO_EMAIL_HOST` tanımlı değilse gitmez**, sessizce konsola yazılır.
6. Tarayıcı konsolunda CORS hatası yok.

3 ve 4'ü tarayıcısız da sınayabilirsin (yönlendirme kuralı için yeterli):

```bash
for p in / /denemeler /sifre-sifirla/abc/def /gizlilik; do
  printf '%-24s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' https://lgs.rehberim.xyz$p)"
done
```

CORS'u da gerçek adreslerle, tarayıcının yaptığı ön kontrolün aynısıyla:

```bash
curl -s -D - -o /dev/null -X OPTIONS \
  -H 'Origin: https://lgs.rehberim.xyz' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type' \
  https://api-lgs.rehberim.xyz/api/auth/token/ | grep -i 'access-control-allow-origin'
```

14 Ekim 2026'da dördü de 200 döndü ve ön kontrol
`access-control-allow-origin: https://lgs.rehberim.xyz` verdi.
