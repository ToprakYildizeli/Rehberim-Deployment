# E-posta — Resend

Şifre sıfırlama e-postaları buradan gider. **Bu, üründeki tek hesap kurtarma
yoludur:** profil ekranında e-posta kilitli olduğu için şifresini unutan
kullanıcının başka çıkışı yok. Çalışmazsa kullanıcı hesabını kaybeder.

## Kurulum

1. Resend'de hesap aç, `rehberim.xyz` alan adını ekle.
2. Resend'in verdiği SPF ve DKIM kayıtlarını DNS'e gir → [`dns.md`](dns.md).
3. Alan adı **doğrulandı** görünene kadar bekle (dakikalar sürebilir).
4. SMTP bilgilerini al ve Railway'e gir:

```
DJANGO_EMAIL_HOST=<Resend'in verdiği sunucu>
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=<Resend'in verdiği kullanıcı>
DJANGO_EMAIL_HOST_PASSWORD=<Resend API anahtarı>
DJANGO_EMAIL_USE_TLS=1
DJANGO_DEFAULT_FROM_EMAIL=Rehberim <noreply@rehberim.xyz>
```

`DJANGO_EMAIL_HOST` **tanımsızsa** Django e-postaları konsola yazar — yerelde
istenen budur, üretimde sessiz bir arıza demektir. Kurulumun asıl kontrolü bu
değişkenin dolu olmasıdır.

## Sıfırlama bağlantısının adresi

```
DJANGO_PASSWORD_RESET_URL=https://rehberim.xyz/sifre-sifirla/{uid}/{token}
```

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

## Kota

Resend'in ücretsiz katı günde 100, ayda 3.000 mail. Şifre sıfırlama dışında mail
göndermiyoruz; bu ölçek uzun süre yeter. İleride haftalık özet e-postası gibi bir
şey eklenirse kota yeniden değerlendirilmeli.
