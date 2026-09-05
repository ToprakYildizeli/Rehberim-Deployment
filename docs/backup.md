# Yedekleme ve geri yükleme

> **İlk dağıtımdan önce okunur.** Geri yükleyemediğin bir yedek, yedek değildir.

Yedeklenmesi gereken iki şey var:

| Ne | Nerede | Kaybedilirse |
|---|---|---|
| PostgreSQL | Railway eklentisi | **Her şey** — hesaplar, programlar, denemeler, konu takibi |
| Yüklemeler (`/app/media`) | Railway volume | Profil fotoğrafları (telafi edilebilir) |

Kod yedeklenmez — GitHub'da duruyor.

## Veritabanı yedeği

Railway'in kendi otomatik yedeklerini aç. Ona ek olarak, elle bir kopya:

```bash
pg_dump "$DATABASE_URL" --format=custom --file="rehberim-$(date +%Y%m%d).dump"
```

`DATABASE_URL` olarak Railway'in **dış** adresini kullan (iç adres yalnız
konteynerlerin içinden çözülür).

⚠️ Dump dosyası hesapların tamamını içerir — kişisel veri. Şifreli bir yerde
tut, bu repo'ya ya da herhangi bir git deposuna **koyma**.

## Geri yükleme provası — atlanmaz

Yedeğin çalıştığını, ona ihtiyaç duyduğun gün öğrenemezsin. Provayı **boş bir
veritabanına** yap, üretime değil:

```bash
# 1. Yerelde bos bir PostgreSQL
docker run -d --name rehberim-restore -e POSTGRES_DB=rehberim \
  -e POSTGRES_USER=rehberim -e POSTGRES_PASSWORD=rehberim \
  -p 5433:5432 postgres:17-alpine

# 2. Yedegi geri yukle
pg_restore --dbname "postgresql://rehberim:rehberim@127.0.0.1:5433/rehberim" \
  --no-owner --clean --if-exists rehberim-YYYYMMDD.dump

# 3. Uygulama bu veriyle acilyor mu
cd <Rehberim-Backend>/Django
DATABASE_URL='postgresql://rehberim:rehberim@127.0.0.1:5433/rehberim' \
  pipenv run python manage.py migrate --check

# 4. Temizle
docker rm -f rehberim-restore
```

`migrate --check` uygulanmamış migration olup olmadığını söyler: yedek eski bir
şemadansa burada anlaşılır.

**Provayı en az bir kez yap ve tarihini aşağıya yaz.**

| Tarih | Yedek | Sonuç |
|---|---|---|
| — | — | henüz prova yapılmadı |

## Yüklemeler

Railway volume'ünün içeriğini düzenli olarak dışarı al. Avatarlar kritik değil;
kaybolursa kullanıcılar yeniden yükler. Ama volume'ün **bağlı olduğunu**
doğrulamak kritik: bağlı değilse her dağıtımda silinirler ve bu sessizce olur.

```bash
scripts/smoke.sh https://api.rehberim.xyz   # once temel akislar
```

Sonra bir profil fotoğrafı yükle, **yeni bir dağıtım yap**, fotoğrafın hâlâ
orada olduğunu gör. Volume'ün gerçekten çalıştığının tek kanıtı budur.

## Ne sıklıkta

Kullanıcı sayısı azken haftalık yeterli. Gerçek öğrenci verisi girmeye
başladığında günlüğe çık — bir haftalık program ve deneme kaydını yeniden
girmek kimsenin yapmak isteyeceği bir şey değil.
