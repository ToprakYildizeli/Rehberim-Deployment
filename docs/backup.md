# Yedekleme ve geri yükleme

> **İlk dağıtımdan önce okunur.** Geri yükleyemediğin bir yedek, yedek değildir.

## Nasıl yürür — üç kademe

Yedekleme tek bir şey değil, **üç ayrı kademedir** ve her biri başka bir
felakete karşı durur. Ölçü iki sayı:

- **RPO** (ne kadar veri kaybedilebilir): son yedekten beri geçen süre.
- **RTO** (ne kadar süre ayakta olmayabilir): geri yüklemenin aldığı süre.

| Kademe | Neye karşı | RPO | Kimde durur |
|---|---|---|---|
| 1. Sağlayıcının anlık görüntüsü + PITR | donanım arızası, yanlışlıkla `DELETE`, bozulan migration | dakikalar | Railway |
| 2. Mantıksal döküm, **başka bir yerde** | sağlayıcının kendisini kaybetmek, hesabın kapanması, faturanın ödenmemesi | bir gün | bizde |
| 3. Geri yükleme provası | *"yedek vardı ama açılmadı"* | — | bizde |

Kademeler birbirinin yerine geçmez. PITR en küçük kaybı verir ama **Railway'in
içinde durur** — hesap kapanırsa o da gider. Mantıksal döküm sağlayıcıdan
bağımsızdır ama en çok bir günlük kaybı kabul eder. Prova olmadan ikisi de
yalnızca bir varsayımdır.

⚠️ **Normalde üretim yedeği dizüstünden alınmaz.** Olağan düzen: kademe 1
sağlayıcıda açıktır, kademe 2'yi bulutta çalışan zamanlanmış bir iş nesne
depolamasına (S3/R2/B2) yazar, kademe 3 ayda bir koşulur. Buradaki
`scripts/yedek-al.sh` **ad hoc araç**: göç öncesi emniyet kopyası, bir şeyi
denemeden önceki kopya, elle alınan haftalık kopya. Zamanlanmış işin yerine
geçmez (sebebi aşağıda: macOS launchd `~/Desktop`'ı okuyamıyor).

**Bugünkü durum (15 Ekim 2026):**

| Kademe | Durum |
|---|---|
| 1. PITR | LGS'de **açık** · YKS'de **bekliyor** (Postgres yeniden dağıtımı gerekiyor) |
| 2. Nesne depolamasına günlük döküm | kod hazır ve uçtan uca doğrulandı, **servis kurulmadı** — [`../yedek-servisi/`](../yedek-servisi/README.md) |
| 3. Prova | **otomatik ve geçiyor** — `scripts/yedek-prova.sh` |

⚠️ **Railway'in anlık görüntü takvimi bu hesapta kullanılamıyor:**
`pitr schedule set` *"Manual backups and backup schedules are only available
for Pro workspaces"* diyor. PITR'in sürekli WAL arşivi çalışıyor, ama elle ya
da takvimli tam görüntü alınamıyor. Kademe 2 bu yüzden isteğe bağlı değil.

**İki ürün, iki ayrı veritabanı.** YKS ve LGS ayrı Railway projelerinde, ayrı
PostgreSQL eklentileriyle çalışıyor. Yedek de ayrı alınır; bir ürünün dökümü
diğerine geri yüklenemez (şemalar farklı, `AUTH_USER_MODEL` bile ayrı).

Yedeklenmesi gereken iki şey var:

| Ne | Nerede | Kaybedilirse |
|---|---|---|
| PostgreSQL | Railway eklentisi | **Her şey** — hesaplar, programlar, denemeler, konu takibi |
| Yüklemeler (`/app/media`) | Railway volume | Profil fotoğrafları (telafi edilebilir) |

Kod yedeklenmez — GitHub'da duruyor.

## Veritabanı yedeği

### Betikle (olağan yol)

```bash
cd ~/Desktop/Rehberim/Rehberim-Backend-LGS      # ya da Rehberim-Backend (YKS)
../Rehberim-Deployment/scripts/yedek-al.sh lgs  # ya da: yks
```

Betik (`scripts/yedek-al.sh`) tüneli açar, dökümü alır, **dosyanın gerçekten
okunabildiğini doğrular** ve üretimdeki satır sayılarını yazdırır. Hiçbir şey
yazmaz; üretimde çalıştırmak güvenlidir. Dosya
`~/Desktop/Rehberim/yedekler/<ürün>-<proje>-<tarih>.dump` olarak, `chmod 600`
ile kaydedilir; yanına satır sayımlarını taşıyan bir `.sayim` dosyası düşer
(provada karşılaştırılan şey o).

Ürün öneki şart: Railway'in ürettiği proje adı tek başına hangi ürün olduğunu
söylemiyor — YKS'nin projesi `gleaming-manifestation`.

- ⚠️ **Yanlış ürünü dökme koruması var:** betik bağlı Railway projesinin
  **adına** bakıyor, klasör adına değil. `yedek-al.sh yks` komutunu LGS'ye
  bağlı bir dizinde çalıştırırsan durur. Dosya adı da projenin adını taşır,
  yani dökümün hangi üründen geldiği dosyadan okunur.
- YKS tarafı için **bir kez** `railway link` gerekiyor (LGS deposu bağlı).
- Döküm **boş da olabilir** ve bu sessiz bir arıza olurdu; betik bu yüzden
  `pg_restore --list` ile nesne sayar ve her tablonun satır sayısını `count(*)`
  ile okur. Beklediğinden küçük bir sayı görürsen dosyayı saklama, sebebini bul.
  - Sayım `n_live_tup` ile **yapılmıyor**: o istatistik tablosundan geliyor ve
    yaklaşıktır, yani provada birebir karşılaştırmaya elvermez.
- **Saklama varsayılan olarak kapalı** (`YEDEK_SAKLA=0`). Gün sayısı verilirse
  o günden eski yedekler silinir, ama **en yeni iki yedek her koşulda
  korunur** — betik uzun süre koşmadıysa elde hiç yedek kalmasın diye.

Ölçülen çalıştırmalar (15 Ekim 2026): YKS 384 KB · 358 nesne · 40 tablo
(5957 görev, 2335 konu takibi, 98 kullanıcı) · LGS 192 KB · 311 nesne ·
34 tablo (üretim henüz boş, karar gereği).

### Elle (betik çalışmazsa)

**Sürüm uyarısı.** Üretimde PostgreSQL **18** çalışıyor
(`ghcr.io/railwayapp-templates/postgres-ssl:18`). `pg_dump` sunucudan **eski
olamaz**; Homebrew'in varsayılan `postgresql@16`'sı bu veritabanını dökemez:

```bash
brew install libpq   # 18.x istemci; /opt/homebrew/opt/libpq/bin altında, PATH'e girmez
```

**Dışarı açmaya gerek yok.** Postgres servisinin genel adresi (`DATABASE_PUBLIC_URL`)
tanımlı değil ve öyle kalmalı. Railway CLI SSH üzerinden geçici bir tünel açıyor:

```bash
railway connect Postgres --tunnel-only --port 55432
```

Komut bağlantı bilgilerini yazdırır ve Ctrl+C'ye kadar açık kalır. Başka bir
kabukta:

```bash
export PGPASSWORD='<tünelin yazdırdığı şifre>'
/opt/homebrew/opt/libpq/bin/pg_dump -h 127.0.0.1 -p 55432 -U postgres -d railway \
  --format=custom --file="rehberim-$(date +%Y%m%d).dump"
```

**Railway'in kendi sürekli yedeği (PITR) şu an KAPALI** — `railway postgres pitr
status --service Postgres`. Açılması ayrı bir depolama kovası ve ek ücret
gerektiriyor; karar verilmedi. O açılana kadar tek koruma bu elle yedek.

⚠️ Dump dosyası hesapların tamamını içerir — kişisel veri. Şifreli bir yerde
tut, bu repo'ya ya da herhangi bir git deposuna **koyma**.

## Geri yükleme provası — atlanmaz

### Betikle (olağan yol)

```bash
scripts/yedek-prova.sh            # her üründen en yeni yedeği dener
scripts/yedek-prova.sh <dosya>    # belirli bir yedeği
```

Geçici bir PostgreSQL 18 konteyneri açıp yedeği oraya yükler, sonra siler.
**Üretime dokunmaz.** Dört şey denetlenir, dördü de ayrı bir sessiz arızaya
karşılık geliyor:

1. `pg_restore` hatasız bitiyor mu — dosya bozuk/yarım olabilir.
2. Satır sayıları yedeğin yanındaki `.sayim` dosyasıyla **birebir** tutuyor mu
   — şema doğru olup verinin boş gelmesi mümkün.
3. `migrate --check` temiz mi — yedek eski bir şemadan olabilir.
4. Django ORM kayıtları okuyabiliyor mu — tablo dolu, model kırık olabilir.

⚠️ Satır karşılaştırması `yedek-al.sh`'ın ürettiği `<dosya>.dump.sayim`'a
dayanıyor. O dosya yoksa (eski betikle alınmış yedek) karşılaştırma atlanır ve
betik bunu söyler — sessizce geçmez.

⚠️ `pg_isready` konteyner daha `initdb` aşamasındayken bile "hazır" diyor;
betik bu yüzden gerçek bir `select 1` dönene kadar bekliyor. İlk yazımda
`pg_restore` tam bu yüzden *"the database system is starting up"* ile düştü.

### Elle (betik çalışmazsa)

Yedeğin çalıştığını, ona ihtiyaç duyduğun gün öğrenemezsin. Provayı **boş bir
veritabanına** yap, üretime değil:

```bash
# 1. Yerelde bos bir PostgreSQL (surum uretimle ayni olsun)
docker run -d --name rehberim-restore -e POSTGRES_DB=rehberim \
  -e POSTGRES_USER=rehberim -e POSTGRES_PASSWORD=rehberim \
  -p 5433:5432 postgres:18-alpine

# 2. Yedegi geri yukle
PGPASSWORD=rehberim /opt/homebrew/opt/libpq/bin/pg_restore \
  --dbname "postgresql://rehberim:rehberim@127.0.0.1:5433/rehberim" \
  --no-owner --no-privileges --clean --if-exists rehberim-YYYYMMDD.dump

# 3. Uygulama bu veriyle acilyor mu
cd <Rehberim-Backend>/Django
PIPENV_DONT_LOAD_ENV=1 DJANGO_DEBUG=0 DJANGO_SECRET_KEY=prova \
  DATABASE_URL='postgresql://rehberim:rehberim@127.0.0.1:5433/rehberim' \
  pipenv run python manage.py migrate --check

# 4. Temizle
docker rm -f rehberim-restore
```

⚠️ `pg_isready` konteyner daha `initdb` aşamasındayken bile "hazır" diyor.
Provada bu yüzden ilk `pg_restore` *"the database system is starting up"* ile
düştü. Hazır olmayı `psql ... -c "select 1"` ile bekleyin.

`migrate --check` uygulanmamış migration olup olmadığını söyler: yedek eski bir
şemadansa burada anlaşılır. Ayrıca satır sayılarını üretimle karşılaştırın ve
ORM'in veriyi okuyabildiğini doğrulayın — şema doğru olup veri boş gelebilir.

**Provayı en az bir kez yap ve tarihini aşağıya yaz.**

| Tarih | Yedek | Sonuç |
|---|---|---|
| 6 Eylül 2026 | `rehberim-20260906.dump` (148 KB, PostgreSQL 18) | **Geçti.** `pg_restore` hatasız · satır sayıları birebir aynı (3 kullanıcı, 1 rehber, 1 öğrenci, 66 migration) · `migrate --check` temiz · ORM kayıtları okudu (rehber + bağlı öğrenci + avatar) |
| 15 Ekim 2026 | `yks-gleaming-manifestation-20261015-1158.dump` (384 KB) | **Geçti**, `scripts/yedek-prova.sh` ile. `pg_restore` hatasız · 40 tablonun satır sayısı birebir · `migrate --check` temiz · ORM 98 kullanıcı okudu |
| 15 Ekim 2026 | `lgs-rehberim-lgs-20261015-1157.dump` (192 KB) | **Geçti.** 34 tablo birebir · `migrate --check` temiz · ORM 1 kullanıcı okudu (üretim henüz boş) |

## Yüklemeler

Railway volume'ünün içeriğini düzenli olarak dışarı al. Avatarlar kritik değil;
kaybolursa kullanıcılar yeniden yükler. Ama volume'ün **bağlı olduğunu**
doğrulamak kritik: bağlı değilse her dağıtımda silinirler ve bu sessizce olur.

Volume'ün bağlı olduğunu **yeniden dağıtımdan sonra** doğrula. Grafiklerde
"Volume Usage" görünmesi yeterli değil: `/app/media`'ya yazabilmek oranın volume
mü yoksa konteynerin kendi diski mi olduğunu söylemez, ikisinde de yazma çalışır.
Fark yalnız yeni bir konteynerde ortaya çıkar.

```bash
railway ssh
echo "volume testi" > /app/media/test.txt
# --- Railway'de Redeploy ---
railway ssh
cat /app/media/test.txt      # yazi geldiyse kalici
rm /app/media/test.txt       # SILMEYI EN SONA BIRAK
```

⚠️ Test dosyasını **redeploy'dan önce silme.** İlk denemede öyle oldu ve sonuç
"dosya yok" çıktı — volume bozuk sanıldı, oysa dosyayı silen bizdik.

**Yapıldı ve geçti (5 Eylül 2026):** konteyner kimliği değişti, dosya yerinde kaldı.

⚠️ Bu test volume'ün **bağlı** olduğunu doğrular, uygulamanın oraya
**yazabildiğini** değil — `railway ssh` root olarak bağlanır, uygulama değil.
6 Eylül 2026'da fotoğraf yükleme tam bu yüzden 500 döndü; bkz.
[`runbook.md`](runbook.md).

## Ne sıklıkta

Kullanıcı sayısı azken haftalık yeterli. Gerçek öğrenci verisi girmeye
başladığında günlüğe çık — bir haftalık program ve deneme kaydını yeniden
girmek kimsenin yapmak isteyeceği bir şey değil.

**YKS şu an canlı ve gerçek rehber verisi taşıyor; LGS üretimi boş.** Yani
bugünkü kayıp riski tamamen YKS tarafında.

## Otomatikleştirme — launchd `~/Desktop`'ı okuyamıyor

`scripts/yedek-gunluk.sh` iki ürünü birden alıyor, saklama süresini uyguluyor
ve elle çalıştırıldığında sorunsuz çalışıyor (15 Ekim 2026'da doğrulandı).
`launchd/xyz.rehberim.yedek.plist` de hazır. **Ama kurulduğunda çalışmıyor:**

```
/bin/sh: .../Rehberim-Deployment/scripts/yedek-gunluk.sh: Operation not permitted
```

Sebep macOS TCC: launchd kullanıcı ajanları `~/Desktop`'a erişemiyor. Ölçüldü
(15 Ekim 2026) — bir launchd işi içinden:

| Dizin | Sonuç |
|---|---|
| `~/Desktop` | **ENGELLİ** |
| `~/Desktop/Rehberim` | **ENGELLİ** |
| `~/Library/Application Support` | okur |
| `~/<düz bir dizin>` | okur |

Depo `~/Desktop/Rehberim` altında olduğu için zamanlanmış iş hem betiği
çalıştıramıyor hem yedeği oraya yazamıyor. **İşi kurulu bırakmak her gece
sessizce düşen bir iş bırakmak demekti**, o yüzden kaldırıldı
(`launchctl bootout`).

**Seçilen yol: 3 — iş buluta taşındı** (karar: 15 Ekim 2026).
[`../yedek-servisi/`](../yedek-servisi/README.md): her ürünün Railway
projesinde bir cron servisi, döküm `age` ile şifrelenip nesne depolamasına
yazılıyor. Aşağıdaki 1 ve 2 kayıt için duruyor.

Üç çıkış yolu var:

1. **Betiği ve hedefi `~/Desktop` dışına taşı.** Betikler
   `~/Library/Application Support/Rehberim/bin/`'e kopyalanır, yedekler aynı
   ağacın altına yazılır. ⚠️ `yedek-al.sh` Railway projesini **bağlı dizinden**
   okuyor; depo dizinine girilemeyeceği için proje kimliği `-p` ile verilmeli,
   yani betik bir kurulum dosyasından okuyacak hâle getirilmeli.
2. **`/bin/sh`'e Full Disk Access ver** (Sistem Ayarları → Gizlilik ve
   Güvenlik). Tek satır iş ama **çok geniş bir yetki**: bundan sonra her kabuk
   betiği bütün diske erişir. Önerilmez.
3. **İşi dizüstünden al, buluta koy** — olağan düzen bu (en başa bak). Kademe
   2'nin doğru yeri zaten burası değil.

Seçim yapılmadı.
## Railway'in sürekli yedeği (PITR) — asıl çözüm

Elle/günlük yedek bir **günlük** veri kaybına açık: sabah 3:30'da yedek
alınır, akşam 9'da veritabanı giderse o günün bütün girişi yok olur. PITR
(point-in-time recovery) sürekli WAL arşivi tutuyor, yani kaybedilen süre
dakikalara iner.

```bash
railway postgres pitr status --service Postgres
```

| Proje | Durum (15 Ekim 2026'da ölçüldü) |
|---|---|
| `gleaming-manifestation` (YKS) | **kapalı** — `Status: disabled`, `Bucket wired: no` |
| `rehberim-lgs` (LGS) | **kapalı** — `Status: disabled`, `Bucket wired: no` |

Açmak ayrı bir depolama kovası ve ek ücret gerektiriyor; **karar verilmedi.**

⚠️ **YKS'de artık erteleyecek bir şey yok:** üretimde 98 kullanıcı ve 5957
görev kaydı var (15 Ekim 2026). Bir rehberin haftalık programını ve deneme
geçmişini yeniden girmek kimsenin yapacağı bir iş değil. LGS üretimi hâlâ boş,
yani orada acele yok — ama pilot dershane girildiği gün aynı duruma geliyor.

⚠️ **PITR, kademe 2'nin yerine geçmez.** Railway'in içinde durur: hesap
kapanırsa, fatura ödenmezse ya da sağlayıcı kaybedilirse PITR de gider. İkisi
birden gerekiyor.
