#!/bin/sh
# Gunluk yedek isi (kademe 2): uretim veritabanini doker, sifreler, nesne
# depolamasina yazar, yuklendigini DOGRULAR ve suresi gecmisleri temizler.
#
# Railway'de her urunun projesinde ayri bir cron servisi olarak kosar. Tunel
# gerekmiyor: servis Railway'in ic aginda, veritabanina dogrudan baglaniyor.
#
# Zorunlu ortam degiskenleri:
#   DATABASE_URL      Postgres eklentisinin degiskenine REFERANSLA baglanir
#                     (elle kopyalanmaz; parola donunce referans kendini
#                     gunceller, kopya guncellenmez)
#   URUN              "yks" ya da "lgs" — dosya adina ve yola giriyor
#   S3_ENDPOINT       orn. https://<hesap>.r2.cloudflarestorage.com
#   S3_BUCKET         kovanin adi
#   S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY
#
# Istege bagli:
#   YEDEK_ANAHTAR     age ACIK anahtari (age1...). Verilirse dokum sifrelenir.
#   SAKLA_GUN         kac gun tutulacak (varsayilan 30)
#   SAGLIK_PING_URL   basarida GET atilacak adres (olu adam dugmesi)
set -eu

eksik=""
for d in DATABASE_URL URUN S3_ENDPOINT S3_BUCKET S3_ACCESS_KEY_ID S3_SECRET_ACCESS_KEY; do
    eval "v=\${$d:-}"
    [ -n "$v" ] || eksik="$eksik $d"
done
[ -z "$eksik" ] || { echo "HATA: eksik degisken:$eksik" >&2; exit 2; }

SAKLA_GUN="${SAKLA_GUN:-30}"
DAMGA="$(date +%Y%m%d-%H%M)"
AD="$URUN-$DAMGA.dump"
GECICI="/tmp/$AD"

echo "[$(date '+%F %T')] $URUN yedegi basliyor"

# --- 1. Dokum ---------------------------------------------------------------
# `--format=custom`: secmeli geri yukleme + sikistirma.
# Parola DATABASE_URL icinde; hicbir yere basilmiyor.
pg_dump "$DATABASE_URL" --format=custom --file="$GECICI"
BOYUT="$(wc -c < "$GECICI" | tr -d ' ')"
echo "  dokum alindi: $BOYUT bayt"

# --- 2. Satir sayimi --------------------------------------------------------
# Sema dogru olup verinin BOS gelmesi mumkun ve bu sessiz bir ariza olurdu.
# Sayim dokumun yanina gidiyor; geri yukleme provasi bununla karsilastiriyor.
# `n_live_tup` DEGIL `count(*)`: ilki istatistikten geliyor ve yaklasiktir.
psql "$DATABASE_URL" -tAq <<'SQL' | sed '/^$/d' | sort > "$GECICI.sayim"
select format('select %L as t, count(*) as n from %I.%I',
              c.relname, n.nspname, c.relname)
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where c.relkind = 'r' and n.nspname = 'public'
\gexec
SQL
TABLO="$(wc -l < "$GECICI.sayim" | tr -d ' ')"
DOLU="$(awk -F'|' '$2 > 0' "$GECICI.sayim" | wc -l | tr -d ' ')"
echo "  sayim: $TABLO tablo, $DOLU tanesi dolu"

# Bos bir dokum sessizce yuklenmesin: hicbir tablosu olmayan bir dokum
# yedek degil, arizadir.
[ "$TABLO" -gt 0 ] || { echo "HATA: dokumde hic tablo yok" >&2; exit 1; }

# --- 3. Sifreleme (anahtar verildiyse) --------------------------------------
# Dosya rehberlerin, ogrencilerin ve velilerin tamamini iceriyor. `age` ACIK
# anahtarla sifreliyor: bu servis dosyayi yazabilir ama GERI OKUYAMAZ. Gizli
# anahtar yalniz sende; servis ele gecse gecmis yedekler okunamaz.
DOKUM="$GECICI"
SAYIM="$GECICI.sayim"
if [ -n "${YEDEK_ANAHTAR:-}" ]; then
    age -r "$YEDEK_ANAHTAR" -o "$GECICI.age" "$GECICI"
    age -r "$YEDEK_ANAHTAR" -o "$GECICI.sayim.age" "$GECICI.sayim"
    rm -f "$GECICI" "$GECICI.sayim"
    DOKUM="$GECICI.age"
    SAYIM="$GECICI.sayim.age"
    echo "  sifrelendi (age)"
else
    echo "  ⚠ SIFRELENMEDI: YEDEK_ANAHTAR tanimli degil. Kisisel veri"
    echo "    saglayici disina duz olarak cikiyor."
fi

# --- 4. Yukleme -------------------------------------------------------------
# rclone yapilandirmasi dosya yerine ortamdan: konteynerde kalici disk yok.
# Yapilandirma dosya yerine ORTAMDAN: konteynerde kalici disk yok.
#
# !! Satir ici baglanti dizesi (`:s3,endpoint=...:kova`) KULLANILMIYOR, iki
#    sebeple: (1) virgulle ayrilan dizge adresteki `:` ve `//` uzerinde
#    kiriliyor ("Custom endpoint `http` was not a valid URI"), (2) gizli
#    anahtar komut satirina girdigi icin `ps` ciktisinda gorunuyor.
export RCLONE_CONFIG=/dev/null
export RCLONE_S3_PROVIDER=Other
export RCLONE_S3_ENDPOINT="$S3_ENDPOINT"
export RCLONE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID"
export RCLONE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY"
export RCLONE_S3_NO_CHECK_BUCKET=true
YOL=":s3:$S3_BUCKET/$URUN"

# Kova erisilebilir mi — YUKLEMEDEN ONCE sorulur. Sorulmazsa rclone ucer kez
# deniyor ve ekrana alti satir yigin izi birakiyor; asil sebep ("kova yok" ya
# da "anahtar yanlis") o yiginin icinde kayboluyor.
if ! rclone lsf "$YOL/" >/dev/null 2>/tmp/s3hata; then
    echo "HATA: nesne depolamasina erisilemiyor ($S3_BUCKET)." >&2
    echo "  Kova var mi, anahtarlar dogru mu, endpoint dogru mu:" >&2
    sed 's/^/    /' /tmp/s3hata >&2
    exit 1
fi

for f in "$DOKUM" "$SAYIM"; do
    [ -f "$f" ] || continue
    rclone copyto "$f" "$YOL/$(basename "$f")" -q
done
echo "  yuklendi: $S3_BUCKET/$URUN/$(basename "$DOKUM")"

# --- 5. Yuklendigini dogrula ------------------------------------------------
# "rclone hata vermedi" ile "dosya orada ve tam" ayni sey degil. Boyut
# karsilastirilmazsa yarim yuklenen bir dosya yedek sanilir.
UZAK_BOYUT="$(rclone size "$YOL/$(basename "$DOKUM")" --json 2>/dev/null \
    | sed -n 's/.*"bytes":\([0-9]*\).*/\1/p')"
YEREL_BOYUT="$(wc -c < "$DOKUM" | tr -d ' ')"
if [ "${UZAK_BOYUT:-0}" = "$YEREL_BOYUT" ]; then
    echo "  ✓ dogrulandi: $UZAK_BOYUT bayt"
else
    echo "HATA: yuklenen boyut tutmuyor (yerel $YEREL_BOYUT, uzak ${UZAK_BOYUT:-yok})" >&2
    exit 1
fi

# --- 6. Saklama -------------------------------------------------------------
# En yeni iki yedek her kosulda korunur: is uzun sure kosmadiysa elde hic
# yedek kalmasin diye.
KALAN="$(rclone lsf "$YOL/" 2>/dev/null | grep -c '\.dump' || true)"
if [ "${KALAN:-0}" -gt 2 ]; then
    rclone delete "$YOL/" --min-age "${SAKLA_GUN}d" -q 2>/dev/null || true
    echo "  saklama: ${SAKLA_GUN} gunden eskiler silindi"
fi

rm -f /tmp/"$URUN"-*.dump* 2>/dev/null || true

# --- 7. Olu adam dugmesi ----------------------------------------------------
# Gunluk kimse okumuyor. Bir izleyici (healthchecks.io gibi) bu ping'i
# beklenen saatte almazsa HABER VERIYOR. Yedeklemede asil tehlike isin
# dusmesi degil, DUSTUGUNUN FARK EDILMEMESI.
if [ -n "${SAGLIK_PING_URL:-}" ]; then
    wget -q -O /dev/null --timeout=10 "$SAGLIK_PING_URL" \
        && echo "  saglik ping'i gonderildi" \
        || echo "  ⚠ saglik ping'i gonderilemedi (yedek yine de alindi)"
fi

echo "[$(date '+%F %T')] bitti"
