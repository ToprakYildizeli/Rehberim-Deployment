# E-posta — Resend

Şifre sıfırlama e-postaları buradan gider. **Bu, üründeki tek hesap kurtarma
yoludur:** profil ekranında e-posta kilitli olduğu için şifresini unutan
kullanıcının başka çıkışı yok. Çalışmazsa kullanıcı hesabını kaybeder.

> **Kuruldu: 16 Eylül 2026.** Aşağıdaki değerler kurulumun gerçekleşmiş
> hâlidir, öneri değil.

## Kurulum

1. Resend'de hesap aç, `rehberim.xyz` alan adını ekle.
2. Resend'in verdiği DKIM ve SPF kayıtlarını DNS'e gir → [`dns.md`](dns.md).
   **SPF artık TXT değil CNAME** (`send`, `rsend`).
3. Alan adı **doğrulandı** görünene kadar bekle, sonra "Enable Sending".
4. API anahtarı üret (Sending access) ve Railway'e gir:

```
DJANGO_EMAIL_HOST=smtp.resend.com
DJANGO_EMAIL_PORT=2587
DJANGO_EMAIL_HOST_USER=resend
DJANGO_EMAIL_HOST_PASSWORD=<Resend API anahtarı>
DJANGO_EMAIL_USE_TLS=1
DJANGO_DEFAULT_FROM_EMAIL=Rehberim <noreply@rehberim.xyz>
DJANGO_PASSWORD_RESET_URL=https://www.rehberim.xyz/sifre-sifirla/{uid}/{token}
```

`DJANGO_EMAIL_HOST` **tanımsızsa** Django e-postaları konsola yazar — yerelde
istenen budur, üretimde sessiz bir arıza demektir. Kurulumun asıl kontrolü bu
değişkenin dolu olmasıdır.

## ⚠️ Railway 587'yi engelliyor — port 2587

**İlk kurulumda mail hiç gitmedi ve site kilitlenme riskine girdi.** Sebep:
Railway'den `smtp.resend.com:587`'ye çıkış açılmıyor. Bağlantı reddedilmiyor,
**hiç dönmüyor**:

```
File "smtplib.py", line 318, in _get_socket
    return socket.create_connection((host, port), timeout, ...)
File "socket.py", line 859, in create_connection
    sock.connect(sa)
...
File "gunicorn/workers/base.py", line 199, in handle_abort
    sys.exit(1)
SystemExit: 1
"POST /api/auth/password-reset/ HTTP/1.1" 500 0
[INFO] Worker exiting (pid: 8)
```

**Çözüm:** `DJANGO_EMAIL_PORT=2587`. Resend bu alternatif portu (ve 2465'i)
tam olarak sağlayıcı engeli için veriyor. 2587'de mail ilk denemede gitti.

**Yan hasar ve kalıcı önlem:** her deneme bir gunicorn işçisini öldürüyordu;
`WEB_CONCURRENCY=3` ile üç eşzamanlı istek bütün API'yi kilitlerdi — yani
"şifremi unuttum"a basan üç kullanıcı siteyi düşürebilirdi. Django/smtplib'in
soket zaman aşımı varsayılanı **süresiz beklemek**. Bunun için
`EMAIL_TIMEOUT` eklendi (varsayılan 10 sn, `DJANGO_EMAIL_TIMEOUT`).

2587 de bir gün engellenirse sıradaki adım SMTP'yi bırakıp Resend'in **HTTPS
API**'sine geçmek: 443 çıkışının çalıştığı kesin (Sentry oradan gidiyor),
küçük bir Django e-posta arka ucu yeter.

## LGS tarafı — 16 Ekim 2026'da kuruldu

Aynı Resend hesabı, **ayrı API anahtarı** (`rehberim-lgs-prod`, Sending
access, yalnız `rehberim.xyz` alan adına kısıtlı). Anahtar paylaşılmadı:
deponun `SECRET_KEY` kuralının aynısı — *bir anahtarın sızması diğerini de
düşürmemeli*. Kota yine de aynı hesapta paylaşılıyor; değişen şey
iptal edilebilirlik.

`rehberim-lgs` projesinde, `rehberim-backend-lgs` servisinde:

```
DJANGO_EMAIL_HOST=smtp.resend.com
DJANGO_EMAIL_PORT=2587
DJANGO_EMAIL_HOST_USER=resend
DJANGO_EMAIL_HOST_PASSWORD=<rehberim-lgs-prod anahtarı>
DJANGO_EMAIL_USE_TLS=1
DJANGO_EMAIL_TIMEOUT=10
DJANGO_DEFAULT_FROM_EMAIL=Rehberim LGS <noreply@rehberim.xyz>
DJANGO_PASSWORD_RESET_URL=https://lgs.rehberim.xyz/sifre-sifirla/{uid}/{token}
```

Gönderen adı **"Rehberim LGS"** — öğretmen hangi üründen posta geldiğini
görmeli. Sıfırlama adresi **dershane panelini** gösteriyor, rehber web'ini
değil.

⚠️ **Port yine 2587.** YKS'deki engelin aynısı; LGS aynı Railway altyapısında
ve 587 orada da açılmıyor.

**Doğrulama (16 Ekim 2026, uçtan uca):** `lgs.rehberim.xyz/sifremi-unuttum` →
gerçek bir adrese istek → posta **~30 saniyede** geldi → bağlantıdan yeni
şifre belirlendi → giriş yapıldı. Günlükte SMTP hatası ya da işçi ölümü yok.

```
00:30:50  POST /api/auth/password-reset/          200
00:31:22  POST /api/auth/password-reset/confirm/  400   ← aşağıdaki not
00:31:53  POST /api/auth/password-reset/confirm/  200
```

Aradaki `400` bir arıza değil: `UserAttributeSimilarityValidator` yeni şifreyi
**kullanıcı adına benzediği için** reddetti. Django'nun
`AUTH_PASSWORD_VALIDATORS` zinciri sıfırlama akışında da çalışıyor, yani
kullanıcı sıfırlama sırasında kolay bir şifreye kaçamıyor — istenen davranış
bu. İleti Türkçe geliyor (`LANGUAGE_CODE = "tr"`) ve panel sunucunun metnini
olduğu gibi gösteriyor.

## Sıfırlama bağlantısının adresi

```
DJANGO_PASSWORD_RESET_URL=https://www.rehberim.xyz/sifre-sifirla/{uid}/{token}
```

⚠️ **Tanımsız bırakma.** Varsayılanı `http://localhost:5173/...` — e-posta
gider ama içindeki bağlantı kullanıcının kendi makinesini gösterir. Sessiz
arıza. `www` yazılıyor: kök alan adı `www`'ye 308 ile dönüyor, e-postadaki
bağlantının gereksiz bir yönlendirmeden geçmesine gerek yok.

`{uid}` ve `{token}` sunucu tarafından doldurulur. Adres **rehber web'ini**
göstermeli: öğrenci ve veli de bağlantıyı telefonunun tarayıcısında açıp orada
sıfırlıyor, mobil derin bağlantı kurulmadı (karar: 4 Eylül 2026).

Bağlantı bir gün geçerli (`DJANGO_PASSWORD_RESET_TIMEOUT`, saniye).

## Doğrulama — atlanmaz

Kurulum bittikten sonra **gerçek bir Gmail ve gerçek bir Outlook adresine**
sıfırlama isteği gönder:

1. `https://rehberim.xyz/sifremi-unuttum` → adresi gir
2. Mail **gelen kutusuna** mı düştü, gereksiz postaya mı? İkincisiyse DNS
   kayıtlarından biri eksik ya da yanlış.
3. Bağlantıya tıkla, yeni şifre belirle, o şifreyle giriş yap.

⚠️ `.xyz` uzantısı bu adımda en çok sıkıntı çıkarabilecek yer. Gereksiz postaya
düşüyorsa SPF, DKIM ve DMARC'ın üçünü birden kontrol et — biri eksikse yeter.

## Hız sınırı

Sıfırlama uçları IP başına 5/saat sınırlı (`DJANGO_THROTTLE_PASSWORD_RESET`).
Kendini test ederken bu sınıra takılabilirsin; aşınca `429` döner ve bir süre
beklemek gerekir. Sınırı test için geçici yükseltmek yerine beklemek daha iyi —
sınırın çalıştığını da doğrulamış olursun.

## Hangi mailler gidiyor

| Mail | Tetikleyici | Alıcı |
|---|---|---|
| Şifre sıfırlama bağlantısı | `POST /auth/password-reset/` | isteyen |
| **Şifreniz değişti** | şifre değiştirme **ve** sıfırlama onayı | hesap sahibi |
| Hoş geldiniz (rol başına 3 metin) | kayıt | kaydolan |
| Hesabına bir veli bağlandı | veli bağlanması | öğrenci **ve** rehberi |
| Hesabınız silindi | hesap silme | silinen hesabın adresi |

Şablonlar: `Django/accounts/templates/email/`, gönderim
`Django/accounts/notifications.py`.

⚠️ **Maile akademik veri yazılmaz** — net, konu ilerlemesi, program içeriği
yok. Reşit olmayan çocuğun verisini yanlış adrese gidebilecek bir kanala
taşımak olurdu; bir test şablonları bu kelimelere karşı tarıyor
(`NotificationEmailTests.test_no_academic_data_in_notification_bodies`).

⚠️ **Şifre sıfırlama dışındaki mailler gönderilemezse işlem geri alınmaz.**
Hoş geldiniz maili gitmedi diye kaydın `500` dönmesi, kullanıcıya
sağladığından çok zarar verirdi. Hata yutulurken **loglanıyor**, Sentry
görüyor.

## Kota

Resend'in ücretsiz katı günde 100, ayda 3.000 mail. Bugünkü mail kümesi
kullanıcı başına birkaç taneden ibaret (kayıtta 1, güvenlik olaylarında 1);
bir sınıfın aynı gün kaydolması ~30 mail eder, tavan 100. Bu ölçek uzun süre
yeter.

İleride **haftalık özet** gibi düzenli bir mail eklenirse hesap yeniden
yapılmalı: 200 öğrencilik bir kurumda veliye haftalık tek mail bile ayda 800
eder ve günlük 100 sınırına tek seferde çarpar (hepsi pazartesi gider).
O noktada ya ücretli kata geçilir ya gönderim güne yayılır.
