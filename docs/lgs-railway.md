# LGS backend'ini Railway'e kurma

Kaynak: `ToprakYildizeli/Rehberim-Backend-LGS` · Hedef: `api-lgs.rehberim.xyz`

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
  görünce Nixpacks'i devre dışı bırakıp onu kullanır — istediğimiz de budur,
  imaj bizim denetimimizde.

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
- Sertifika ancak DNS çözüldükten sonra çıkar; birkaç dakika sürebilir.

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

---

## Henüz yapılmayanlar

- **E-posta (Resend).** Tanımlanmazsa postalar konsola yazılır ve şifresini
  unutan öğretmen sıfırlama bağlantısını hiç almaz. YKS ile aynı Resend
  hesabı kullanılabilir; ayrı bir gönderen adresi (`noreply@rehberim.xyz`
  yeter) ve **port 2587** gerekir — Railway 587'yi engelliyor, ayrıntı
  [`email-resend.md`](email-resend.md).
- **Sentry.** LGS kodunda Sentry entegrasyonu yok (YKS'de var).
- **Yedekleme provası.** [`backup.md`](backup.md) yordamı LGS veritabanı için
  de uygulanmalı. *Yedeği geri yükleyemiyorsan yedeğin yok.*
- **HSTS.** HTTPS'in çalıştığı gözle doğrulandıktan sonra
  `DJANGO_HSTS_SECONDS=31536000`.
