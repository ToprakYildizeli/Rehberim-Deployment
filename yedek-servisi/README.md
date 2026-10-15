# Yedek servisi — Railway cron

Kademe 2'nin çalıştığı yer: üretim veritabanını her gün döküp **Railway
dışındaki** bir nesne depolamasına yazan küçük bir iş. Genel resim:
[`../docs/backup.md`](../docs/backup.md).

> ⚠️ Bu depo normalde **kod içermez.** Bu dizin bilinçli istisna: iş dağıtım
> altyapısının parçası, hiçbir sır içermiyor (her değer ortam değişkeninden
> geliyor) ve uygulama kodunun bir kopyası değil.

## Ne yapıyor

1. `pg_dump` ile dökümü alır (**tünel yok** — servis Railway'in iç ağında).
2. Her tablonun satır sayısını `count(*)` ile okuyup dökümün yanına yazar.
   Provada karşılaştırılan şey bu; şema doğru olup verinin boş gelmesi
   mümkün ve bu sessiz bir arıza olurdu.
3. Hiç tablosu olmayan bir döküm yüklenmeden **durur**.
4. `age` ile şifreler (anahtar verildiyse).
5. Nesne depolamasına yazar.
6. **Yüklendiğini doğrular** — uzak boyut yerel boyutla karşılaştırılır.
   "rclone hata vermedi" ile "dosya orada ve tam" aynı şey değil.
7. Saklama süresi geçmişleri siler, **en yeni ikisini her koşulda koruyarak.**
8. Sağlık ping'i atar (varsa).

Her adım başarısızlıkta **sıfır olmayan kodla çıkıyor**; Railway dağıtımı
"crashed" gösteriyor.

## Kurulum (her ürün için ayrı servis)

Ürünün **kendi Railway projesinde** yeni bir servis:

| Ayar | Değer |
|---|---|
| Kaynak | `ToprakYildizeli/Rehberim-Deployment` |
| Kök dizin | `yedek-servisi` |
| Cron Schedule | `30 3 * * *` |
| Bölge | veritabanıyla aynı (Europe West) |

⚠️ **Servis ürünün kendi projesinde olmalı**, ayrı bir projede değil:
`DATABASE_URL` ancak aynı projedeki eklentiye referansla bağlanabiliyor ve iç
ağ adresi proje dışından çözülmüyor.

### Ortam değişkenleri

| Değişken | Değer |
|---|---|
| `DATABASE_URL` | Postgres eklentisinin değişkenine **referansla** (`${{Postgres.DATABASE_URL}}`) |
| `URUN` | `yks` ya da `lgs` |
| `S3_ENDPOINT` | örn. `https://<hesap>.r2.cloudflarestorage.com` |
| `S3_BUCKET` | kovanın adı |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | kovanın anahtarı |
| `YEDEK_ANAHTAR` | `age` **açık** anahtarı (`age1...`) |
| `SAKLA_GUN` | varsayılan `30` |
| `SAGLIK_PING_URL` | (istege bağlı) başarıda GET atılacak adres |

⚠️ `DATABASE_URL` **elle kopyalanmaz.** Parola döndüğünde referans kendini
günceller, kopya güncellenmez — ve bunu ancak yedek sessizce durduğunda
öğrenirsin.

⚠️ Kova **önceden açılmış olmalı.** İş `CreateBucket` yetkisi istemiyor
(`--s3-no-check-bucket`); kova yoksa yüklemeden önce okunur bir hatayla durur.

### Şifreleme anahtarı

```bash
age-keygen -o rehberim-yedek-anahtar.txt     # brew install age
```

Çıktının **açık** anahtarı (`age1...`) servise `YEDEK_ANAHTAR` olarak
yazılır. **Gizli anahtar hiçbir yere yazılmaz** — şifre yöneticisine koy.

Neden açık anahtarla: servis yedeği yazabiliyor ama **geri okuyamıyor.**
Servis ya da kova ele geçse geçmiş yedekler okunamaz. Simetrik bir parola
kullanılsaydı aynı sır hem yazma hem okuma yetkisi verirdi.

⚠️ **Gizli anahtarı kaybetmek bütün yedekleri kaybetmektir.** Şifrelenmiş
dökümü başka hiçbir şey açamaz. Anahtarı yedeklerden *ayrı* bir yerde tut.

## Geri yükleme

```bash
rclone copy :s3:<kova>/yks/ .                      # ya da lgs/
age -d -i rehberim-yedek-anahtar.txt -o y.dump yks-<tarih>.dump.age
age -d -i rehberim-yedek-anahtar.txt -o y.sayim yks-<tarih>.dump.sayim.age
```

Sonra `../scripts/yedek-prova.sh y.dump` — satır sayımı yanındaki `.sayim`
dosyasıyla karşılaştırılır.

## Doğrulandı (15 Ekim 2026)

Zincirin tamamı yerelde uçtan uca koşturuldu: üretimden alınmış gerçek YKS
dökümü (5957 görev, 40 tablo) → `pg_dump` → `age` ile şifreleme → S3 uyumlu
depolamaya yükleme → boyut doğrulaması → indirme → şifre çözme → boş bir
PostgreSQL 18'e geri yükleme → **40 tablonun satır sayısı birebir**, görev
sayısı 5957.

Yol boyunca çıkan ve düzeltilen üç şey, bir daha düşülmesin diye:

1. **Alpine sürümü `postgresql18-client`'a göre seçildi.** 3.21 ve 3.22'de o
   paket yok (yalnız 17) ve `pg_dump` sunucudan eski olamaz. 3.23 tam
   üretimdeki sürümü veriyor (18.6).
2. **rclone satır içi bağlantı dizesi kullanılmıyor.** Virgülle ayrılan dizge
   adresteki `:` ve `//` üzerinde kırılıyor (*"Custom endpoint `http` was not
   a valid URI"*) ve gizli anahtar komut satırına girdiği için `ps` çıktısında
   görünüyor. Yapılandırma `RCLONE_S3_*` ortam değişkenlerinden.
3. **Kova erişimi yüklemeden önce sorulur.** Sorulmazsa rclone üç kez deniyor
   ve ekrana altı satır yığın izi bırakıyor; asıl sebep ("kova yok" / "anahtar
   yanlış") o yığının içinde kayboluyor.
