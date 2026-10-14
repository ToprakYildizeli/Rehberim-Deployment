# Yedekleme ve geri yükleme

> **İlk dağıtımdan önce okunur.** Geri yükleyemediğin bir yedek, yedek değildir.

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
`~/Desktop/Rehberim/yedekler/<proje>-<tarih>.dump` olarak, `chmod 600` ile
kaydedilir.

- ⚠️ **Yanlış ürünü dökme koruması var:** betik bağlı Railway projesinin
  **adına** bakıyor, klasör adına değil. `yedek-al.sh yks` komutunu LGS'ye
  bağlı bir dizinde çalıştırırsan durur. Dosya adı da projenin adını taşır,
  yani dökümün hangi üründen geldiği dosyadan okunur.
- YKS tarafı için **bir kez** `railway link` gerekiyor (LGS deposu bağlı).
- Döküm **boş da olabilir** ve bu sessiz bir arıza olurdu; betik bu yüzden
  `pg_restore --list` ile nesne sayar ve `pg_stat_user_tables`'dan satır
  sayılarını basar. Beklediğinden küçük bir sayı görürsen dosyayı saklama,
  sebebini bul.
- Betik **saklama/silme yapmıyor** (bilerek): eski yedekleri otomatik silen
  bir betik, bir gün tek sağlam yedeği de siler. Dizini elle gözden geçir.

İlk çalıştırma (14 Ekim 2026, LGS üretimi): 192 KB · 311 nesne · katalog
dışında satır yok — üretim veritabanı henüz boş, karar gereği.

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

## Otomatikleştirme (launchd)

Elle alınan yedek, alınmayı hatırladığın sürece yedektir. Günlük bir iş
tanımla — `cron` değil `launchd`, macOS'ta uyuyan makinede kaçan işi
sonra çalıştıran tek yol o.

`~/Library/LaunchAgents/xyz.rehberim.yedek.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>xyz.rehberim.yedek</string>
  <key>ProgramArguments</key><array>
    <string>/bin/sh</string>
    <string>-lc</string>
    <string>cd ~/Desktop/Rehberim/Rehberim-Backend &amp;&amp; ../Rehberim-Deployment/scripts/yedek-al.sh yks</string>
  </array>
  <key>StartCalendarInterval</key><dict>
    <key>Hour</key><integer>3</integer><key>Minute</key><integer>30</integer>
  </dict>
  <key>StandardOutPath</key><string>/tmp/rehberim-yedek.log</string>
  <key>StandardErrorPath</key><string>/tmp/rehberim-yedek.log</string>
</dict></plist>
```

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/xyz.rehberim.yedek.plist
launchctl kickstart -p gui/$(id -u)/xyz.rehberim.yedek   # hemen bir kez calistir
```

⚠️ **Günlüğü ara ara oku** (`/tmp/rehberim-yedek.log`). Sessizce başarısız olan
bir yedek işi, hiç kurulmamış bir yedek işinden kötüdür: "yedeğim var"
sanırsın. `railway` oturumu da süresi dolabilir — günlükte ilk görülecek şey o.

⚠️ **Laptop yedeği gerçek bir yedek stratejisi değil.** Dosya tek makinede
duruyor; o makine kaybolursa yedek de kaybolur. Asıl çözüm Railway'in sürekli
yedeği (aşağıda); laptop yedeği onun yerine değil, **yanına** geçer.

## Railway'in sürekli yedeği (PITR) — asıl çözüm

Elle/günlük yedek bir **günlük** veri kaybına açık: sabah 3:30'da yedek
alınır, akşam 9'da veritabanı giderse o günün bütün girişi yok olur. PITR
(point-in-time recovery) sürekli WAL arşivi tutuyor, yani kaybedilen süre
dakikalara iner.

```bash
railway postgres pitr status --service Postgres
```

| Proje | Durum (14 Ekim 2026) |
|---|---|
| YKS | **kapalı** |
| `rehberim-lgs` | **kapalı** (`Bucket wired: no`) |

Açmak ayrı bir depolama kovası ve ek ücret gerektiriyor; **karar verilmedi.**
Gerçek dershane ve rehber verisi girdikçe bu karar ertelenemez hâle geliyor:
iki ürünün verisi de yeniden girilebilir türden değil.
