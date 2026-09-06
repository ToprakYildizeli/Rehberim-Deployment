# Yedekleme ve geri yükleme

> **İlk dağıtımdan önce okunur.** Geri yükleyemediğin bir yedek, yedek değildir.

Yedeklenmesi gereken iki şey var:

| Ne | Nerede | Kaybedilirse |
|---|---|---|
| PostgreSQL | Railway eklentisi | **Her şey** — hesaplar, programlar, denemeler, konu takibi |
| Yüklemeler (`/app/media`) | Railway volume | Profil fotoğrafları (telafi edilebilir) |

Kod yedeklenmez — GitHub'da duruyor.

## Veritabanı yedeği

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
