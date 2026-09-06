# Backend'i Railway'e kurma

Kaynak: `ToprakYildizeli/Rehberim-Backend` · Hedef: `api.rehberim.xyz`

Railway arayüzü zaman zaman değişiyor; aşağıdaki adımlarda **kavramlar** esastır,
menü adları değil. Değerlerin kendisi (yol, port, değişken adı) sabittir.

---

## 1. Servisi oluştur

- Yeni proje → GitHub repo'sundan dağıt → **`Rehberim-Backend`**
- **Bölge: Europe West.** Kullanıcılar Türkiye'de; ABD bölgesi her isteğe
  ~150 ms ekler ve KVKK'nın yurt dışına aktarım tarafını zorlaştırır.
- **Kök dizin (root directory): `Django`**

  Bu adım atlanırsa dağıtım başarısız olur: `Dockerfile` depo kökünde değil,
  `Django/` altında. Railway `Dockerfile`'ı görünce Nixpacks'i devre dışı
  bırakıp onu kullanır — istediğimiz de budur, imaj bizim denetimimizde.

## 2. PostgreSQL ekle

- Projeye PostgreSQL eklentisi ekle.
- Backend servisinin `DATABASE_URL` değişkenini eklentinin kendi değişkenine
  **referansla** bağla (elle kopyalama; parola döndüğünde referans kendini
  günceller, kopya güncellenmez).
- **İç ağ adresini tercih et.** Railway hem iç (`*.railway.internal`) hem dış
  adres verir; dış adres üzerinden gitmek gereksiz gecikme ve veri ücreti demek.

Ayar dosyamız `postgresql://` şemasını ve `?sslmode=` gibi parametreleri
çözüyor (`Django/settings.py` → `_database_from_url`). Ek bir şey gerekmez.

## 3. Kalıcı disk (volume) bağla

- Bağlama noktası: **`/app/media`**
- Ortam değişkeni: `DJANGO_MEDIA_ROOT=/app/media`

⚠️ **Bu adım atlanırsa profil fotoğrafları her dağıtımda silinir.** Konteynerin
dosya sistemi geçicidir; yüklemeler diskte durmalı. 5 GB avatar için fazlasıyla
yeter.

⚠️ **Disk root'a ait bağlanır.** Uygulama root olarak çalışmadığı için sahipliği
açılışta `docker-entrypoint.sh` düzeltiyor. Panelde yapılacak bir şey yok, ama
fotoğraf yükleme 500 dönüyorsa ilk bakılacak yer burası — bkz.
[`runbook.md`](runbook.md).

Ayrı bir web sunucusu olmadığı için yüklemeleri Django'nun kendisi servis eder:
`DJANGO_SERVE_MEDIA=1`. Verimli değil ama avatar ölçeğinde sorun çıkarmaz.

## 4. Ortam değişkenleri

Tam liste ve yer tutucular: [`../env/backend.env.example`](../env/backend.env.example)

`DJANGO_SECRET_KEY` için yeni bir anahtar üret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

⚠️ **Depodaki eski anahtarı kullanma.** `django-insecure-...` ile başlayan o
değer git geçmişinde duruyor, yanmış sayılır.

`DJANGO_DEBUG` **tanımlanmaz** (ya da `0`). Ayar dosyası tanımsızsa DEBUG'ı
kapalı sayar; `SECRET_KEY` veya `DATABASE_URL` eksikse uygulama sessizce yanlış
çalışmak yerine açılmaz ve sebebini söyler.

## 5. Sağlık yoklaması

- **Yol: `/healthz`**

⚠️ **İlk kurulumda iki tuzak buraya takıldı (5 Eylül 2026), ikisi de çözüldü:**

1. `DJANGO_ALLOWED_HOSTS`'a **platformun kendi adresi de girilmeli.** Yoklama
   konteyner'a iç ağdan, genel adresten farklı bir `Host` başlığıyla geliyor;
   yalnız genel adres yazılırsa Django her yoklamaya `400` döner ve dağıtım
   "1/1 replicas never became healthy" ile iptal edilir. Django baştaki noktayı
   alt alan adı jokeri sayar:
   `DJANGO_ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}},.railway.app`
2. Yoklama **düz HTTP ile ve `X-Forwarded-Proto` başlığı olmadan** geliyor, yani
   HTTPS yönlendirmesine takılıp `301` dönerdi. `SECURE_REDIRECT_EXEMPT` ile
   yalnız `/healthz` muaf tutuldu (backend'de, `settings.py`).

**Port:** Railway kendi `PORT` değerini enjekte ediyor ve giriş betiği ona uyuyor
(gunicorn `8080`'i dinledi). Alan adının **hedef portu buna eşit olmalı** — kutuya
başka bir değer yazılırsa sağlık yoklaması iç ağdan geçtiği için dağıtım başarılı
görünür ama **genel adres dışarıdan açılmaz**. `PORT` değişkenini elle tanımlama.

Railway yeni sürümü canlıya almadan önce buraya sorar; `200` gelmezse eski sürüm
ayakta kalır. Uç veritabanına da bakar (`SELECT 1`), yani PostgreSQL'e
ulaşamayan bir sürüm canlıya alınmaz.

## 6. Alan adı

- Servise özel alan adı ekle: **`api.rehberim.xyz`**
- Railway bir CNAME hedefi verir; onu DNS'e gir → [`dns.md`](dns.md)
- Sertifika kendiliğinden çıkar (birkaç dakika sürebilir)

Alan adı çalıştıktan **sonra** şu değişkenler doldurulur:

```
DJANGO_ALLOWED_HOSTS=api.rehberim.xyz
DJANGO_CSRF_TRUSTED_ORIGINS=https://api.rehberim.xyz
DJANGO_CORS_ALLOWED_ORIGINS=https://rehberim.xyz,https://www.rehberim.xyz
```

CORS yalnız tarayıcıyı ilgilendirir — mobil uygulamalar buraya yazılmaz.

## 7. Doğrula

```bash
scripts/smoke.sh https://api.rehberim.xyz
```

Sonra yönetici hesabı aç (Railway'in kabuk/komut özelliğiyle):

```bash
python manage.py createsuperuser
```

## 8. En son: HSTS

HTTPS'in çalıştığını **gözünle gördükten sonra**:

```
DJANGO_HSTS_SECONDS=31536000
```

⚠️ Sırayı bozma. HSTS bir kez yayınlandığında tarayıcılar süresi dolana dek bu
alan adına düz HTTP ile bağlanmayı reddeder; sertifikada bir sorun çıkarsa geri
dönüşü yoktur.

---

## Migration'lar

Konteyner her açılışta `migrate` çalıştırır (`Django/docker-entrypoint.sh`).
Tek kopyada sorun değil. **Birden çok kopyaya (replica) çıkarsan** aynı anda
açılan konteynerler yarışa girer; o zaman migration'ı ayrı bir "release" adımına
taşı ve entrypoint'ten çıkar.

## Bilinen sınırlar

- **Hız sınırı sayacı işlem başına.** Şifre sıfırlamadaki 5/saat sınırı
  varsayılan yerel önbellekte tutuluyor; `WEB_CONCURRENCY=3` ile gerçek sınır
  15/saate çıkar. Paylaşımlı bir önbellek (Redis) eklenene kadar böyle.
- **Sayfalama yok.** Listeler tabloyu bütün döndürüyor; öğrenci sayısı büyürse
  yanıtlar şişer.
