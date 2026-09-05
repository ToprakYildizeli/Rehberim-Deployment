# Hata izleme — Sentry

Bir şey patladığında haberdar olmanın tek yolu. `SENTRY_DSN` tanımlanmazsa Sentry
**hiç devreye girmez** — yani kurmadan da uygulama çalışır, sadece kör kalırsın.

## Kurulum

1. Sentry'de hesap aç, **Django** projesi oluştur.
2. Verdiği DSN'i Railway'e gir:

```
SENTRY_DSN=<Sentry'nin verdigi DSN>
SENTRY_ENVIRONMENT=production
```

3. Bir dağıtım yap ve hatanın gerçekten düştüğünü gör (aşağıya bak).

Railway commit özetini `RAILWAY_GIT_COMMIT_SHA` olarak veriyor; kod bunu Sentry'ye
sürüm olarak geçiriyor, yani hangi dağıtımın patladığı belli oluyor. Ekstra bir
şey yapman gerekmez.

## Kişisel veri — burası önemli

Bu uygulama **reşit olmayan öğrencilerin** verisini işliyor. Sentry'nin kendi
varsayılanları istek gövdesini gönderiyor; `POST /api/auth/login/` gövdesinde
**açık şifre**, kayıt gövdesinde ad, soyad ve e-posta var.

Kod bunu üç katmanla kapatıyor (`Django/observability.py`):

| Katman | Ne yapıyor |
|---|---|
| `send_default_pii=False` | Kullanıcı kimliği, IP ve çerezler gönderilmez |
| `max_request_body_size="never"` | İstek gövdesi hiç gönderilmez |
| `before_send=scrub_event` | `Authorization`/`Cookie` başlıkları ve `token`/`uid` sorgu anahtarları temizlenir |

Üçüncüsü ilk ikisine güvenmemek için var: SDK varsayılanları sürümler arasında
değişiyor.

⚠️ **Sentry arayüzünden "PII gönder" gibi bir ayarı açma.** Koddaki koruma
sunucu tarafında; arayüzden açılan bir ayar bunu delmez ama kafa karışıklığı
yaratır. Yeni bir alan hassaslaşırsa kaynak repo'daki `SENSITIVE_HEADERS` /
`SENSITIVE_QUERY_KEYS` listelerine eklenir.

## Kota

Performans izleme **varsayılan olarak kapalı** (`SENTRY_TRACES_SAMPLE_RATE=0`).
Açılırsa ücretsiz kat hiç hata olmadan da dolar. Gerekirse küçük bir oranla:

```
SENTRY_TRACES_SAMPLE_RATE=0.05
```

## Çalıştığını doğrula

Sentry'yi kurduktan sonra gerçekten olay düştüğünü gör — kurulup çalışmayan bir
izleyici, hiç kurmamaktan daha kötü, çünkü haberdar olduğunu sanırsın.

Railway'in kabuğundan:

```bash
python -c "import sentry_sdk; sentry_sdk.capture_message('kurulum testi')"
```

Sentry panelinde birkaç saniye içinde görünmeli. Görünmüyorsa DSN yanlış ya da
girilmemiştir.

Sonra gerçek bir hata denemesi yap ve **olayın içinde şifre ya da JWT olmadığını
gözünle doğrula.** Koruma testli ama canlıda bir kez bakmaya değer.
