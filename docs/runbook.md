# Runbook — dağıtım sonrası ve arıza anı

## Her dağıtımdan sonra

```bash
scripts/smoke.sh https://api.rehberim.xyz
```

Sonra elle iki şey:

- Rehber web'inde giriş yap
- `/panel`'de F5'e bas (SPA yönlendirmesi)

## Canlı adresler

| Ne | Adres |
|---|---|
| API | `https://api.rehberim.xyz/api` |
| Sağlık ucu | `https://api.rehberim.xyz/healthz` |
| Admin | `https://api.rehberim.xyz/admin/` |
| Rehber web | `https://www.rehberim.xyz` |
| Yedek (Railway) | `https://rehberim-backend-production.up.railway.app` |

Railway'in geçici adresi bilerek bırakıldı: alan adı tarafında bir şey bozulursa
elde çalışan ikinci bir kapı kalsın diye. `ALLOWED_HOSTS` ikisini de kabul ediyor.

Mobil uygulamalar derlenirken:
`--dart-define=API_BASE_URL=https://api.rehberim.xyz/api`

## Canlı adresler — LGS (14 Ekim 2026'dan beri)

LGS **ayrı bir üründür**: ayrı Railway projesi, ayrı PostgreSQL, ayrı Sentry
projesi. Bir arıza anında yanlış projeye bakmak en sık hata.

| Ne | Adres |
|---|---|
| API | `https://api-lgs.rehberim.xyz/api` |
| Sağlık ucu | `https://api-lgs.rehberim.xyz/healthz` |
| Admin | `https://api-lgs.rehberim.xyz/admin/` |
| Dershane paneli | `https://lgs.rehberim.xyz` |
| Yedek (Railway) | `https://rehberim-backend-lgs-production.up.railway.app` |
| Yedek (Vercel) | `https://rehberim-frontend-lgs.vercel.app` |

```bash
scripts/smoke-lgs.sh https://api-lgs.rehberim.xyz
```

Sonra elle: panelden giriş + `/denemeler`de F5.

⚠️ Giriş ucu `/api/auth/token/` (YKS'de `/api/auth/login/`), CORS değişkeninin
adı `CORS_ALLOWED_ORIGINS` (YKS'de `DJANGO_CORS_ALLOWED_ORIGINS`). Komutları
hafızadan yazarken ikisi de karışıyor.

## Kesinti gerektiren işi ne zaman yapmalı

Veritabanını yeniden başlatan işler (PITR açma, sürüm yükseltme, disk
değişikliği) için **hafta içi 04:00–06:00**.

Ölçüm (15 Ekim 2026, bir haftalık gunicorn erişim günlüğü, bot ve statik
istekler ayıklanmış — 1442 gerçek `/api/` isteği):

| Saat | İstek | Saat | İstek |
|---|---|---|---|
| 00–02 | **0** | 13:00 | 180 |
| 03:00 | 1 | 14:00 | 101 |
| 04–06 | **0** | 17:00 | 107 |
| 07:00 | 51 | 20:00 | 86 |
| 10:00 | 185 | **21:00** | **219 — hafta zirvesi** |
| 12:00 | 92 | 22:00 | 91 |

⚠️ **"Gece" yanlış bir sezgi:** 21:00 haftanın en yoğun saati. Bu bir çalışma
takip uygulaması — öğrenciler akşam çalışıyor, ders çalışıp kaydını o saatte
giriyor. Gerçekten sessiz olan pencere **01:00–06:00**.

⚠️ **Hafta sonu da yanlış sezgi:** Cumartesi 359, Pazar 337 istek; Pazartesi
36, Salı 55. Hafta sonu zirve, hafta içi sakin — aynı sebeple.

Ölçümü tekrarlamak için:

```bash
cd Rehberim-Backend && railway logs -d --since 7d --lines 5000 > /tmp/erisim.log
```

Sonra saat alanına (`[GG/Ay/YYYY:SS`) göre say; bot'ları `User-Agent`'tan
(`bot|crawler|spider|AdsBot|ChatGPT-User`) ve `/api/` dışı yolları ayıkla.
Ayıklanmazsa tablo yanlış çıkıyor: günlüğün **%38'i** bot taraması
(`.env`, `/@fs/...` arayan tarayıcılar — hepsi `404`, sızan bir şey yok).

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
| Fotoğraf yükleme 500, günlükte traceback yok | Volume root'a ait, uygulama yazamıyor | Aşağıdaki bölüm |
| Şifre sıfırlama maili gelmiyor | SMTP tanımsız ya da DNS eksik | `DJANGO_EMAIL_HOST`, [`email-resend.md`](email-resend.md) |
| Mail geliyor ama gereksiz postada | SPF/DKIM/DMARC eksik | [`dns.md`](dns.md) |
| Sıfırlama bağlantısı 404 | SPA yönlendirmesi yok | [`web-deploy.md`](web-deploy.md) |
| Sıfırlama isteği 429 | Hız sınırı (IP başına 5/saat) | Beklenen davranış, bekle |
| Yeni alan adında her istek 400 | `DJANGO_ALLOWED_HOSTS`'ta yok | Variables — alan adı eklenince güncellenmeli |
| Arayüz açılıyor, "Kayıt başarısız" | Yeni alan adı CORS listesinde yok | `DJANGO_CORS_ALLOWED_ORIGINS` |
| Yeni alan adı sertifika hatası | Sertifika henüz çıkmadı | Birkaç dakika bekle; Railway/Vercel doğrulamayı bitirsin |
| Admin formu "CSRF doğrulaması başarısız" | `DJANGO_CSRF_TRUSTED_ORIGINS` eksik | Variables |
| Sertifika saatlerce "doğrulanıyor" | `_railway-verify.<alt alan>` TXT kaydı yok | [`dns.md`](dns.md) |
| Railway "repository not accessible", dallar yüklenmiyor | Özel depoya GitHub App izni yok | [`lgs-railway.md`](lgs-railway.md) §1 |
| `main`'e push edildi, dağıtım hiç başlamadı | Dağıtım tetikleyicisi oluşmamış (`repoTriggers: []`) | Servis → Source → yeniden bağla |
| Açılışta "No migrations to apply" ama veritabanı yeni | Büyük ihtimalle günlük akışı satırları yuttu | Duman testi: 401 geliyorsa şema yerinde |

## ⚠️ Bağlanan disk root'a ait gelir

**Belirti (6 Eylül 2026):** `POST /api/auth/me/avatar/` → 500, gövde boş HTML,
erişim günlüğünde yalnız `500 145`.

Railway volume'ü konteynerin dışından bağlar ve dizin `root:root 755` olur;
imajın kendi sahiplik ayarı bu bağlamayla üzerine yazılır. Uygulama root
olarak çalışmadığı için altına klasör açamaz.

**Yanıltıcı yanı:** `railway ssh` **root** olarak bağlanır. Elle
`touch /app/media/deneme` çalışır, uygulama yine de yazamaz. Kontrol ederken
kullanıcıya bakın:

```bash
railway ssh "ls -ldn /app/media"
```

Sahip `10001 10001` olmalı. `0 0` görüyorsanız giriş betiğindeki `chown`
çalışmamış demektir — açılış günlüğünde `UYARI: ... sahipliği düzeltilemedi`
satırını arayın.

Düzeltme `docker-entrypoint.sh` içinde: konteyner root açılır, `chown` yapar,
`setpriv` ile uid 10001'e düşer. Ayrıntı: `Rehberim-Backend/docs/deployment.md`.

## ⚠️ Railway her zaman son commit'i çekmiyor

**5 Eylül 2026'da yaşandı ve bir saat kaybettirdi.** Bir ortam değişkeni
eklendiğinde Railway yeniden dağıttı, ama `main`'in ucunu değil **son dağıtımın
kaynağını** yeniden derledi — üç commit geride bir sürümü. O sürümde sağlık
ucunun yönlendirme muafiyeti yoktu, yoklama `301` aldı, hiçbir replika sağlıklı
sayılmadı ve adres `"Application not found"` döndürmeye başladı.

Kafa karıştıran şey şuydu: **kodda hiçbir sorun yoktu.** `origin/main`'de
düzeltme duruyordu, aynı imaj yerelde üretilip Railway'in gönderdiği isteğin
birebir aynısı atıldığında `200` dönüyordu.

**Bir dağıtım açıklanamaz biçimde başarısız olduğunda İLK bakılacak yer
Deployments → Source satırındaki commit özetidir.** `main`'in ucu değilse sorun
kodda değil, Railway'in ne derlediğindedir.

Panele girmeden de sorulabilir:

```bash
railway status --json | grep -o '"commitHash":"[^"]*"' | head -1
```

Çıkan özeti `git rev-parse HEAD` ile karşılaştırın; tutmuyorsa boş bir commit
atıp (`git commit --allow-empty`) yeniden dağıtım tetikleyin.

Çözüm: arayüzden "deploy latest commit", ya da `main`'e boş bir commit atıp
tetiklemek:

```bash
git commit --allow-empty -m "Railway'i son commit'i çekmeye zorla"
git push
```

## Yeni dağıtımdan hemen sonra 404 görmek normal

Eski konteyner kaldırılıp yenisi ayağa kalkana dek adres kısa süre `404`
döndürebilir; duman testi o aralıkta çalışırsa yanıltıcı hata verir. Bir dakika
bekleyip tekrar çalıştır. (Volume bağlı olduğu için Railway kesintisiz geçiş
yapamıyor — bir volume aynı anda tek konteynere bağlanabiliyor.)

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
