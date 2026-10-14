# LGS backend'ini Railway'e kurma

Kaynak: `ToprakYildizeli/Rehberim-Backend-LGS` · Hedef: `api-lgs.rehberim.xyz`

**Durum: kuruldu ve canlı (14 Ekim 2026).** Aşağıdaki adımlar o gün
uygulandı; takılınan iki yer (GitHub izni ve sertifika doğrulaması) ilgili
adımlarda uyarı olarak duruyor.

> **LGS, YKS'den tamamen ayrı bir üründür.** Kod paylaşılmıyor, veritabanı
> paylaşılmıyor. Bu yüzden **ayrı bir Railway projesi** ve **ayrı bir
> PostgreSQL** açılır. Aynı projeye ikinci bir servis olarak eklemek, iki
> ürünün değişkenlerini ve veritabanlarını karıştırma riski demektir.

Railway arayüzü zaman zaman değişiyor; aşağıdaki adımlarda **kavramlar**
esastır, menü adları değil. Değerlerin kendisi (yol, port, değişken adı)
sabittir.

---

## YKS kurulumundan farkları

Önce bunlar, çünkü YKS yordamını hafızadan uygulamak hataya yol açar:

| | YKS | LGS |
|---|---|---|
| Kök dizin (root directory) | `Django` | **repo kökü** — boş bırak |
| Kalıcı disk (volume) | `/app/media` gerekli | **gerekmiyor** |
| `DJANGO_MEDIA_ROOT`, `DJANGO_SERVE_MEDIA` | gerekli | **tanımlanmaz** |
| Giriş ucu | `/api/auth/login/` | `/api/auth/token/` |
| Sağlık ucu | `/healthz` | `/healthz` (aynı) |

Disk gerekmemesinin sebebi: LGS'de kullanıcı yüklemesi yok. Hiçbir modelde
`FileField`/`ImageField` yoktur, PDF karne okunup atılıyor — diske yazılmıyor.
Bu yüzden LGS imajında `USER` da var (YKS'de bilerek yoktu, yetki giriş
betiğinde bırakılıyordu).

---

## 1. Servisi oluştur

- Yeni **proje** → GitHub repo'sundan dağıt → **`Rehberim-Backend-LGS`**
- **Bölge: Europe West.** Kullanıcılar Türkiye'de; ABD bölgesi her isteğe
  ~150 ms ekler ve KVKK'nın yurt dışına aktarım tarafını zorlaştırır.
- **Kök dizin: boş bırak.** `Dockerfile` repo kökünde. Railway `Dockerfile`'ı
  görünce seçili derleyiciyi (bugün Railpack) devre dışı bırakıp onu kullanır —
  istediğimiz de budur, imaj bizim denetimimizde. Arayüzde "Builder: Railpack"
  yazması sorun değil; derleme günlüğünde kendi katmanlarımızı (`pipenv
  install --deploy`, `collectstatic`) görüyorsan doğru imaj derleniyor demektir.
  Railpack'e düşmüş olsaydı `docker-entrypoint.sh` hiç çalışmaz, yani
  **migration da collectstatic da atlanırdı.**
- **Bölge servis ayarında.** Proje oluştururken sorulmuyor: servis → Settings →
  Scale → *Regions & Replicas*. CLI'da bölge seçeneği yok. PostgreSQL'i
  eklemeden önce ayarla — diski sonradan taşımak istemezsin.

⚠️ **Depo özelse Railway'in GitHub uygulamasına o depo için izin verilmelidir.**
14 Ekim 2026'da yarım saat kaybettirdi. Belirtiler:

- Settings → Source'ta "Could not load branches. Retry"
- Dağıtım tetiklenemiyor: `Repository "..." not found or is not accessible`
- Servis oluşmuş ve depo adı yazıyor ama **dağıtım tetikleyicisi yok**
  (`repoTriggers: []`) — yani `main`'e push edince de hiçbir şey olmaz

Düzeltme: GitHub → Settings → Applications → Railway → Configure → *Repository
access* → depoyu ekle. Sonra Railway'de servisin kaynağını **yeniden bağla**;
izin verilmeden önce kurulan bağlantı kendiliğinden düzelmiyor.

## 2. PostgreSQL ekle

- Projeye PostgreSQL eklentisi ekle. **YKS'nin veritabanı kullanılmaz.**
- Servisin `DATABASE_URL` değişkenini eklentinin kendi değişkenine
  **referansla** bağla (elle kopyalama; parola döndüğünde referans kendini
  günceller, kopya güncellenmez).
- **İç ağ adresini tercih et** (`*.railway.internal`); dış adres üzerinden
  gitmek gereksiz gecikme ve veri ücreti demek.

Ayar dosyası `postgresql://` şemasını ve `?sslmode=` gibi parametreleri
çözüyor (django-environ). Ek bir şey gerekmez.

⚠️ **Üretim veritabanı boş başlar.** Geliştirme makinesindeki `db.sqlite3`
üretime taşınmıyor (karar: 10 Ekim 2026) — her dershane kendi hesabını kayıt
ekranından açıyor ve kurumu sunucu görünmez biçimde oluşturuyor.

## 3. Ortam değişkenleri

Tam liste ve yer tutucular:
[`../env/lgs-backend.env.example`](../env/lgs-backend.env.example)

`DJANGO_SECRET_KEY` için yeni bir anahtar üret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

⚠️ **Depodaki `django-insecure-dev-only-change-in-prod` değerini kullanma.**
Git geçmişinde duruyor, yanmış sayılır.

⚠️ **YKS'nin anahtarını da kullanma.** İki ürün ayrı; bir anahtarın sızması
diğerini de düşürmemeli.

`DJANGO_DEBUG` **tanımlanmaz** (ya da `0`). Ayar dosyası tanımsızsa DEBUG'ı
kapalı sayar; `SECRET_KEY` veya `DATABASE_URL` eksikse uygulama sessizce
yanlış çalışmak yerine **açılmaz** ve sebebini söyler.

## 4. Sağlık yoklaması

- **Yol: `/healthz`**

⚠️ **YKS kurulumunda buraya iki tuzak takıldı (5 Eylül 2026); ikisi de LGS
kodunda baştan çözülmüş durumda, ama panel tarafı sizde:**

1. `DJANGO_ALLOWED_HOSTS`'a **platformun kendi adresi de girilmeli.** Yoklama
   konteyner'a iç ağdan, genel adresten farklı bir `Host` başlığıyla geliyor;
   yalnız genel adres yazılırsa Django her yoklamaya `400` döner ve dağıtım
   "1/1 replicas never became healthy" ile iptal edilir. Django baştaki
   noktayı alt alan adı jokeri sayar:

   ```
   DJANGO_ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}},.railway.app,api-lgs.rehberim.xyz
   ```

2. Yoklama **düz HTTP ile ve `X-Forwarded-Proto` başlığı olmadan** geliyor,
   yani HTTPS yönlendirmesine takılıp `301` dönerdi. `SECURE_REDIRECT_EXEMPT`
   ile `healthz` muaf tutuldu — kodda duruyor, bir şey yapmanız gerekmez.

## 5. Alan adını bağla

- Railway → servis → alan adı ekranı → **`api-lgs.rehberim.xyz`**
- Verdiği CNAME hedefini DNS panelinde `api-lgs` adıyla tanımla
  (bkz. [`dns.md`](dns.md)).
- **Doğrulama TXT kaydını da gir:** `_railway-verify.api-lgs` → Railway'in
  verdiği `railway-verify=<64 karakter>` değeri.
- Sertifika ancak DNS çözüldükten sonra çıkar; birkaç dakika sürebilir.

⚠️ **CNAME tek başına yetmiyor.** 14 Ekim 2026'da sertifika 20 dakika boyunca
`VALIDATING_OWNERSHIP`'te asılı kaldı: CNAME yayılmıştı (`PROPAGATED`), HTTP
istekleri Railway kenarına ulaşıyordu (80 portundan `301` dönüyordu) ama
`verified: false` duruyordu. Eksik olan şey doğrulama TXT'siydi; girildikten
birkaç dakika sonra `verified: true` ve sertifika `VALID` oldu. YKS'nin çalışan
`api` kaydında da aynı TXT var (`_railway-verify.api`) — yani bu hesapta kural,
istisna değil.

Durumu panele girmeden okumak için:

```bash
railway domain status api-lgs.rehberim.xyz -s rehberim-backend-lgs --json
```

`dnsRecords[].status`, `verification.verified` ve `certificate.status`
alanlarına bak. Alan adında engelleyici bir **CAA kaydı** olmadığını da
doğrula (`dig +short CAA rehberim.xyz`) — varsa Let's Encrypt hiç deneyemez.

Sonra `DJANGO_CSRF_TRUSTED_ORIGINS=https://api-lgs.rehberim.xyz` ve
`CORS_ALLOWED_ORIGINS=https://lgs.rehberim.xyz`.

⚠️ CORS değişkeninin adı **`CORS_ALLOWED_ORIGINS`** — YKS'de
`DJANGO_CORS_ALLOWED_ORIGINS`. İki ayrı kod tabanı, iki ayrı ad.

## 6. Yönetici hesabı

Paket/özellik yönetimi Django admin üzerinden yapılıyor, yani bu hesap olmadan
bir dershanenin paketini kısıtlayamazsınız.

```bash
railway ssh
python manage.py createsuperuser
```

⚠️ `railway run` **değil**: o komut yerel makinede çalışır ve iç ağdaki
veritabanı adresini çözemez.

## 7. Dağıtım sonrası

```bash
scripts/smoke-lgs.sh https://api-lgs.rehberim.xyz
```

Sonra paneli yayına al: [`lgs-web.md`](lgs-web.md).

**Sentry'yi de bağla** (13 Ekim 2026'dan beri kodda var): Sentry'de LGS için
ayrı bir proje aç ve DSN'i `SENTRY_DSN` olarak Railway'e yaz. Tanımlanmazsa
uygulama çalışır ama yakalanmamış istisnanın tek izi sunucu günlüğü olur —
yani bir şeyin bozulduğunu ancak biri söylerse öğrenirsin.

⚠️ İstek gövdesi Sentry'ye hiçbir koşulda gitmiyor (giriş gövdesinde açık
şifre, öğrenci kaydında çocuğun adı, karne içe aktarmada bir sınıfın bütün
adları var). Bu, ayar değil **kodda** sabit.

DSN'i yazdıktan sonra zincirin ucunu da doğrula; Sentry "ilk olayı bekliyor"
durumundayken çalışıp çalışmadığı belli olmaz:

```bash
railway ssh --service rehberim-backend-lgs
python -c "import os,django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); import sentry_sdk; sentry_sdk.capture_message('kurulum testi'); sentry_sdk.flush()"
```

Panelde göründükten sonra kaydı *Resolve* et.

### ⚠️ Açılış günlüğündeki "No migrations to apply" yanıltıcı olabilir

Bomboş bir veritabanına yapılan ilk dağıtımda açılış günlüğünde onlarca
`Applying ... OK` satırı beklenir; 14 Ekim 2026'daki ilk dağıtımda bunun yerine
tek satır `No migrations to apply.` yazdı. Tablolar **oluşmuştu** — duman testi
dokuz maddeyi de geçti, kimliksiz uçlar 401 döndü (tablo olmasa 500 dönerdi) —
yani sorun migration'da değil, Railway'in günlük akışındaydı; derleme
günlüğünde de satırlar tekrar edip eksiliyordu.

**Günlüğe değil, davranışa bak.** Şüpheleniyorsan duman testini çalıştır: giriş
ucu 500 yerine 401 dönüyorsa şema yerindedir.

---

## Henüz yapılmayanlar

- **E-posta (Resend).** Tanımlanmazsa postalar konsola yazılır ve şifresini
  unutan öğretmen sıfırlama bağlantısını hiç almaz. YKS ile aynı Resend
  hesabı kullanılabilir; ayrı bir gönderen adresi (`noreply@rehberim.xyz`
  yeter) ve **port 2587** gerekir — Railway 587'yi engelliyor, ayrıntı
  [`email-resend.md`](email-resend.md).
- **Yedekleme provası.** [`backup.md`](backup.md) yordamı LGS veritabanı için
  de uygulanmalı. *Yedeği geri yükleyemiyorsan yedeğin yok.*
- **HSTS.** HTTPS'in çalıştığı gözle doğrulandıktan sonra
  `DJANGO_HSTS_SECONDS=31536000`.

## Kurulum kayıtları (14 Ekim 2026)

| | |
|---|---|
| Railway projesi | `rehberim-lgs` (YKS projelerinden ayrı) |
| Servis | `rehberim-backend-lgs` · bölge EU West (Amsterdam) |
| Veritabanı | `Postgres` eklentisi, iç ağ: `postgres.railway.internal:5432` |
| Yedek adres | `rehberim-backend-lgs-production.up.railway.app` |
| Sentry projesi | `rehberim-lgs-backend` (yalnız Error monitoring açık) |

Yedek adres bilerek duruyor: alan adı tarafında bir şey bozulursa elde çalışan
ikinci bir kapı kalsın diye. `DJANGO_ALLOWED_HOSTS` ikisini de kabul ediyor.
