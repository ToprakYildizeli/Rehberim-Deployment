# Öğrenci ve veli arayüzü — tarayıcı sürümü

> **Neden var:** mobil uygulamaları mağazaya çıkarmak uzun sürüyor; hoca bu
> arada 5-10 öğrenciyle denemek istiyor (karar: 16 Eylül 2026).
>
> **Yeni bir arayüz yazılmadı.** Flutter uygulamalarının ikisi de web'e
> **olduğu gibi** derleniyor (~16 sn, indirme gzip ile ~0,9 MB). Sıfırdan bir
> React arayüzü yazmak haftalar sürer ve asıl bedeli o değil: aynı API
> sözleşmesini iki istemcide senkron tutmak olurdu. Mobil çıkınca web sürümü
> ya durur ya kapatılır — atılacak kod yok.

## Derleme

```sh
scripts/build-web.sh                        # üretim API'si
scripts/build-web.sh http://127.0.0.1:8000/api   # yerel backend
```

Çıktı: `build/web/{ogrenci,veli}` + kök `index.html`. Betik, derlenen paketin
**içinde doğru API adresinin geçtiğini doğruluyor**; yanlış adresle çıkmak
sessiz bir arıza olurdu (sayfa açılır, giriş çalışmaz).

⚠️ **Dal kontrolü.** Uygulamalar Yunus'un repo'larında ve `ogrenci-tamamlama` /
`veli-app` dallarında duruyor; `main`'den derlersen bu iş için yazılan
ekranların hiçbiri gelmez. Betik hangi dalda olduğunu ekrana yazıyor, oku.

## Barındırma — tek alan adı, iki yol

`app.rehberim.xyz/ogrenci` ve `app.rehberim.xyz/veli`.

İki ayrı alt alan adı yerine tek alan adı: bir DNS kaydı, **bir CORS kökeni**,
bir dağıtım. Uygulamalar tarayıcı adres çubuğunu kullanmıyor (Navigator ile
çalışıyorlar), bu yüzden alt yolda çalışmaları için `--base-href` dışında bir
şey gerekmiyor.

1. Vercel'de yeni proje, **statik** (derleme komutu yok), çıktı klasörü
   `build/web`.
2. Alan adı ekle: `app.rehberim.xyz`.
3. Natro'da CNAME: `app` → Vercel'in verdiği hedef.

Vercel Flutter'ı kendi derleyemez (imajında Flutter yok). Derleme **yerelde**
yapılır, `build/web` yüklenir.

## CORS — atlanırsa hiçbir şey çalışmaz

Mobil uygulamalar CORS'a tabi değildir, **tarayıcı tabidir**. Backend'in
`DJANGO_CORS_ALLOWED_ORIGINS` değişkenine web adresi eklenmeli:

```
DJANGO_CORS_ALLOWED_ORIGINS=https://www.rehberim.xyz,https://app.rehberim.xyz
```

Rehber web'in adresi de listede kalmalı — değişken **tüm** listeyi taşıyor,
üstüne yazmak eskisini siler.

Belirti: sayfa açılır, giriş düğmesi çalışmaz, tarayıcı konsolunda CORS
hatası görünür. Sunucu logunda hiçbir şey olmaz (istek sunucuya ulaşmadan
tarayıcıda durur).

## Bilinen sınırlar

- **Token saklama.** `flutter_secure_storage` web'de Web Crypto + localStorage
  kullanıyor; telefondaki Keychain/Keystore kadar güçlü değil. Sayfada üçüncü
  parti script yok, pilot ölçeğinde kabul edilebilir — ama kalıcı çözüm mobil
  uygulamanın kendisi.
- **İlk açılış** ~0,9 MB (gzip). Sonraki açılışlar önbellekten.
- **Geniş pencere.** Uygulama telefon arayüzü; tarayıcıda 440 piksellik bir
  çerçeveye alınıyor (`lib/common/widgets/web_frame.dart`, `kIsWeb` korumalı).
  Dar pencerede çerçeve kendini kapatıyor.
- **Servis çalışanı önbelleği.** Yeni sürüm yayınlandığında kullanıcı eski
  paketi görebilir; sert yenileme (⌘⇧R) gerekir. Pilot için sorun değil,
  yaygınlaşırsa sürüm damgası düşünülmeli.

## Android alternatifi

Mağazaya hiç gerek yok: APK doğrudan gönderilebilir (`flutter build apk`),
inceleme yok, ücret yok, gerçek uygulama. iOS'ta bu yol kapalı — orada
TestFlight ve Apple Developer hesabı ($99/yıl) gerekiyor.
