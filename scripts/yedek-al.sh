#!/bin/sh
# Uretim veritabaninin yedegini alir ve aldigi yedegin OKUNABILIR oldugunu
# dogrular. Hicbir sey YAZMAZ, yalniz okur — uretimde calistirmak guvenlidir.
#
# Kullanim:
#   cd ~/Desktop/Rehberim/Rehberim-Backend-LGS      # Railway projesine bagli dizin
#   ../Rehberim-Deployment/scripts/yedek-al.sh lgs
#
#   cd ~/Desktop/Rehberim/Rehberim-Backend          # (once: railway link)
#   ../Rehberim-Deployment/scripts/yedek-al.sh yks
#
# Secenekler (ortam degiskeni):
#   YEDEK_DIZIN   dosyalarin yazilacagi yer  (varsayilan ~/Desktop/Rehberim/yedekler)
#   YEDEK_PORT    yerel tunel portu          (varsayilan 55432)
#   PG_DUMP       pg_dump yolu               (varsayilan /opt/homebrew/opt/libpq/bin/pg_dump)
#
# !! Dosya hesaplarin ve ogrencilerin tamamini icerir — kisisel veri.
#    Hicbir git deposuna koyma. `yedekler/` bilerek repo disinda.
set -eu

URUN="${1:-}"
case "$URUN" in
    yks|lgs) ;;
    *) echo "Kullanim: yedek-al.sh <yks|lgs>" >&2; exit 2 ;;
esac

DIZIN="${YEDEK_DIZIN:-$HOME/Desktop/Rehberim/yedekler}"
PORT="${YEDEK_PORT:-55432}"
PG_DUMP="${PG_DUMP:-/opt/homebrew/opt/libpq/bin/pg_dump}"
PG_RESTORE="$(dirname "$PG_DUMP")/pg_restore"
SERVIS=Postgres

# --- 1. Araclar -------------------------------------------------------------
# pg_dump sunucudan ESKI OLAMAZ. Homebrew'in varsayilan postgresql@16'si
# uretimdeki 18'i dokemez ve hata mesaji bunu acikca soylemez.
command -v railway >/dev/null || { echo "railway CLI yok: brew install railway" >&2; exit 1; }
[ -x "$PG_DUMP" ] || { echo "pg_dump yok: $PG_DUMP (brew install libpq)" >&2; exit 1; }

# --- 2. Dogru proje mi ------------------------------------------------------
# En pahali hata: YKS yedegi diye LGS'i dokmek (ya da tersi) ve dosyayi
# yanlis adla saklamak. Bagli projenin ADINA bakiyoruz, klasor adina degil.
PROJE="$(railway status --json 2>/dev/null \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("name",""))' 2>/dev/null || true)"
[ -n "$PROJE" ] || { echo "Bu dizin bir Railway projesine bagli degil. Once: railway link" >&2; exit 1; }

case "$URUN:$PROJE" in
    lgs:*lgs*)  ;;
    yks:*lgs*)  echo "DUR: 'yks' dendi ama bagli proje '$PROJE' (LGS gibi duruyor)." >&2; exit 1 ;;
    yks:*)      ;;
    lgs:*)      echo "DUR: 'lgs' dendi ama bagli proje '$PROJE' LGS degil." >&2; exit 1 ;;
esac

echo "Urun: $URUN · Railway projesi: $PROJE"

# --- 3. Kimlik bilgileri ----------------------------------------------------
# Tunelin kendi yazdirdigi satiri ayristirmak kirilgandi; dogrudan servisin
# kendi degiskenlerini okuyoruz. Parola hicbir yere basilmiyor.
DEG="$(railway variables -s "$SERVIS" --kv 2>/dev/null || true)"
[ -n "$DEG" ] || { echo "'$SERVIS' servisinin degiskenleri okunamadi." >&2; exit 1; }
oku() { printf '%s\n' "$DEG" | sed -n "s/^$1=//p" | head -1; }
PGUSER_="$(oku PGUSER)"; PGDB_="$(oku PGDATABASE)"; PGPASS_="$(oku PGPASSWORD)"
[ -n "$PGUSER_" ] && [ -n "$PGDB_" ] && [ -n "$PGPASS_" ] \
    || { echo "PGUSER/PGDATABASE/PGPASSWORD eksik." >&2; exit 1; }

# --- 4. Tunel ---------------------------------------------------------------
# Veritabani disariya kapali (DATABASE_PUBLIC_URL tanimli degil ve oyle
# kalmali). Railway SSH uzerinden gecici bir tunel aciyor.
mkdir -p "$DIZIN"
GUNLUK="$(mktemp -t railway-tunel)"
railway connect "$SERVIS" --tunnel-only --port "$PORT" >"$GUNLUK" 2>&1 &
TUNEL=$!
temizle() { kill "$TUNEL" 2>/dev/null || true; rm -f "$GUNLUK"; }
trap temizle EXIT INT TERM

printf 'Tunel aciliyor (port %s)' "$PORT"
i=0
until PGPASSWORD="$PGPASS_" "$(dirname "$PG_DUMP")/psql" \
        -h 127.0.0.1 -p "$PORT" -U "$PGUSER_" -d "$PGDB_" -tAc 'select 1' >/dev/null 2>&1; do
    i=$((i + 1)); [ "$i" -gt 40 ] && { echo; echo "Tunel acilmadi:" >&2; cat "$GUNLUK" >&2; exit 1; }
    printf '.'; sleep 1
done
echo " hazir."

# --- 5. Dokum ---------------------------------------------------------------
# `--format=custom`: pg_restore ile secmeli geri yukleme ve sikistirma.
DOSYA="$DIZIN/$PROJE-$(date +%Y%m%d-%H%M).dump"
PGPASSWORD="$PGPASS_" "$PG_DUMP" -h 127.0.0.1 -p "$PORT" -U "$PGUSER_" -d "$PGDB_" \
    --format=custom --file="$DOSYA"
chmod 600 "$DOSYA"   # kisisel veri; baska kullaniciya okutma

# --- 6. Yedek gercekten okunabiliyor mu -------------------------------------
# Bos ya da yarim yazilmis bir dosya da "yedek" gorunur. Icindekiler
# listelenemiyorsa yedek yoktur.
NESNE="$("$PG_RESTORE" --list "$DOSYA" 2>/dev/null | grep -c '^[0-9]' || true)"
[ "${NESNE:-0}" -gt 0 ] || { echo "DOGRULAMA BASARISIZ: dosya okunamiyor ($DOSYA)" >&2; exit 1; }

# Satir sayilari: sema dogru olup verinin bos gelmesi mumkun. Sayilar
# uretimden okunuyor; geri yukleme provasinda bunlarla karsilastirilir.
SAYIM="$(PGPASSWORD="$PGPASS_" "$(dirname "$PG_DUMP")/psql" \
    -h 127.0.0.1 -p "$PORT" -U "$PGUSER_" -d "$PGDB_" -tAc \
    "select coalesce(string_agg(t || '=' || n, ' · ' order by t), 'tablo yok')
     from (select relname as t, n_live_tup as n from pg_stat_user_tables
           where n_live_tup > 0 order by n_live_tup desc limit 8) s" 2>/dev/null || echo '?')"

echo
echo "Yedek alindi: $DOSYA"
echo "  boyut   : $(du -h "$DOSYA" | cut -f1)"
echo "  nesne   : $NESNE"
echo "  satirlar: $SAYIM"
echo
echo "Geri yukleme provasi atlanmaz — docs/backup.md."
