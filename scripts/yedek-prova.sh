#!/bin/sh
# Bir yedegin GERI YUKLENEBILDIGINI kanitlar. Uretime dokunmaz: gecici,
# yerel bir PostgreSQL konteynerine yukler ve sonunda onu siler.
#
# Kullanim:
#   scripts/yedek-prova.sh ~/Desktop/Rehberim/yedekler/yks-...-20261015-1155.dump
#   scripts/yedek-prova.sh            # en yeni yedegi bulur (her urunden)
#
# Dort sey denetlenir — dordu de ayri bir sessiz ariza turune karsilik geliyor:
#   1. pg_restore hatasiz bitiyor mu          (dosya bozuk/yarim olabilir)
#   2. satir sayilari yedegin yanindaki
#      `.sayim` dosyasiyla birebir tutuyor mu (sema dogru, veri bos olabilir)
#   3. `migrate --check` temiz mi             (yedek eski bir semadan olabilir)
#   4. Django ORM kayitlari okuyabiliyor mu   (tablo dolu, model kirik olabilir)
#
# Gereksinim: docker. Uretimdeki surumun AYNISI kullanilir (PostgreSQL 18);
# daha eski bir imaj dokumu hic yukleyemez.
set -eu

DIZIN="${YEDEK_DIZIN:-$HOME/Desktop/Rehberim/yedekler}"
PORT="${PROVA_PORT:-5433}"
IMAJ="${PROVA_IMAJ:-postgres:18-alpine}"
KONTEYNER="rehberim-prova-$$"
PG_RESTORE="${PG_RESTORE:-/opt/homebrew/opt/libpq/bin/pg_restore}"
PSQL="$(dirname "$PG_RESTORE")/psql"
REHBERIM="${REHBERIM_KOK:-$HOME/Desktop/Rehberim}"

command -v docker >/dev/null || { echo "docker yok." >&2; exit 1; }
[ -x "$PG_RESTORE" ] || { echo "pg_restore yok: $PG_RESTORE (brew install libpq)" >&2; exit 1; }

# --- Hangi yedek -----------------------------------------------------------
if [ "$#" -gt 0 ]; then
    YEDEKLER="$*"
else
    # Arguman verilmediyse her urunun en yenisi denenir. Provayi "bugun hangi
    # dosyaydi" diye aramaya baglamak, provanin hic yapilmamasinin yolu.
    YEDEKLER=""
    for u in yks lgs; do
        y="$(ls -1t "$DIZIN/$u-"*.dump 2>/dev/null | head -1 || true)"
        [ -n "$y" ] && YEDEKLER="$YEDEKLER $y"
    done
    [ -n "$YEDEKLER" ] || { echo "$DIZIN icinde yedek bulunamadi." >&2; exit 1; }
fi

TOPLAM_HATA=0

prova() {
    YEDEK="$1"
    [ -f "$YEDEK" ] || { echo "Dosya yok: $YEDEK" >&2; return 1; }
    AD="$(basename "$YEDEK")"
    URUN="$(printf '%s' "$AD" | cut -d- -f1)"
    case "$URUN" in
        yks) KOK="$REHBERIM/Rehberim-Backend/Django"; PY="pipenv run python" ;;
        lgs) KOK="$REHBERIM/Rehberim-Backend-LGS";    PY=".venv/bin/python" ;;
        *)   echo "Dosya adindan urun anlasilmiyor ($AD); 'yks-' ya da 'lgs-' ile baslamali." >&2
             return 1 ;;
    esac

    echo "─────────────────────────────────────────────"
    echo "Prova: $AD  (urun: $URUN)"
    hata=0

    # 1. Bos veritabani --------------------------------------------------
    docker run -d --name "$KONTEYNER" \
        -e POSTGRES_DB=prova -e POSTGRES_USER=prova -e POSTGRES_PASSWORD=prova \
        -p "$PORT:5432" "$IMAJ" >/dev/null
    # shellcheck disable=SC2064
    trap "docker rm -f $KONTEYNER >/dev/null 2>&1 || true" EXIT INT TERM

    URL="postgresql://prova:prova@127.0.0.1:$PORT/prova"
    printf '  veritabani aciliyor'
    i=0
    # !! `pg_isready` konteyner daha initdb asamasindayken "hazir" diyor ve
    #    ilk pg_restore "the database system is starting up" ile dusuyor.
    #    Hazir olmak = gercek bir sorgu donmesi.
    until PGPASSWORD=prova "$PSQL" "$URL" -tAc 'select 1' >/dev/null 2>&1; do
        i=$((i + 1)); [ "$i" -gt 60 ] && { echo " ACILMADI"; docker logs "$KONTEYNER" 2>&1 | tail -5; return 1; }
        printf '.'; sleep 1
    done
    echo " hazir."

    # 2. Geri yukle ------------------------------------------------------
    if PGPASSWORD=prova "$PG_RESTORE" --dbname "$URL" \
            --no-owner --no-privileges --clean --if-exists "$YEDEK" >/dev/null 2>/tmp/prova-restore.$$; then
        echo "  ✓ pg_restore hatasiz"
    else
        echo "  ✗ pg_restore DUSTU:"; tail -5 /tmp/prova-restore.$$ | sed 's/^/      /'
        hata=$((hata + 1))
    fi
    rm -f /tmp/prova-restore.$$

    # 3. Satir sayilari yedegin yanindakiyle birebir mi -------------------
    # Sema dogru olup verinin bos gelmesi mumkun; o yuzden sayim sart.
    if [ -f "$YEDEK.sayim" ]; then
        PGPASSWORD=prova "$PSQL" "$URL" -tAq <<'SQL' 2>/dev/null | sed '/^$/d' | sort > "/tmp/prova-sayim.$$"
select format('select %L as t, count(*) as n from %I.%I',
              c.relname, n.nspname, c.relname)
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where c.relkind = 'r' and n.nspname = 'public'
\gexec
SQL
        if diff -q "$YEDEK.sayim" "/tmp/prova-sayim.$$" >/dev/null 2>&1; then
            echo "  ✓ satir sayilari birebir ($(wc -l < "$YEDEK.sayim" | tr -d ' ') tablo)"
        else
            echo "  ✗ satir sayilari TUTMUYOR (sol: uretim, sag: geri yuklenen):"
            diff "$YEDEK.sayim" "/tmp/prova-sayim.$$" | head -10 | sed 's/^/      /'
            hata=$((hata + 1))
        fi
        rm -f "/tmp/prova-sayim.$$"
    else
        echo "  ! sayim dosyasi yok ($AD.sayim) — bu yedek eski betikle alinmis,"
        echo "    satir karsilastirmasi atlandi."
    fi

    # 4. Sema guncel mi + ORM okuyor mu ----------------------------------
    # Yedek eski bir semadansa `migrate --check` burada soyler.
    if [ -d "$KOK" ]; then
        cikti="$(cd "$KOK" && env PIPENV_DONT_LOAD_ENV=1 DJANGO_DEBUG=0 \
            DJANGO_SECRET_KEY=prova-icin-gecici-anahtar-yeterince-uzun-olsun-2026 \
            DATABASE_URL="$URL" $PY manage.py migrate --check 2>&1)" && {
            echo "  ✓ migrate --check temiz (uygulanmamis migration yok)"
        } || {
            echo "  ✗ migrate --check DUSTU:"; printf '%s\n' "$cikti" | tail -5 | sed 's/^/      /'
            hata=$((hata + 1))
        }

        cikti="$(cd "$KOK" && env PIPENV_DONT_LOAD_ENV=1 DJANGO_DEBUG=0 \
            DJANGO_SECRET_KEY=prova-icin-gecici-anahtar-yeterince-uzun-olsun-2026 \
            DATABASE_URL="$URL" $PY manage.py shell -c '
from django.contrib.auth import get_user_model
print("kullanici:", get_user_model().objects.count())
' 2>&1)" && {
            echo "  ✓ ORM kayitlari okudu — $(printf '%s\n' "$cikti" | sed -n 's/^kullanici: /kullanici: /p' | tail -1)"
        } || {
            echo "  ✗ ORM okuyamadi:"; printf '%s\n' "$cikti" | tail -5 | sed 's/^/      /'
            hata=$((hata + 1))
        }
    else
        echo "  ! $KOK bulunamadi — sema ve ORM denetimi atlandi."
    fi

    docker rm -f "$KONTEYNER" >/dev/null 2>&1 || true
    trap - EXIT INT TERM

    if [ "$hata" -eq 0 ]; then echo "  GECTI."; else echo "  $hata DENETIM BASARISIZ."; fi
    return "$hata"
}

for y in $YEDEKLER; do
    prova "$y" || TOPLAM_HATA=$((TOPLAM_HATA + 1))
done

echo "─────────────────────────────────────────────"
if [ "$TOPLAM_HATA" -eq 0 ]; then
    echo "Butun provalar gecti. Tarihi docs/backup.md'deki tabloya yaz."
else
    echo "$TOPLAM_HATA yedek provayi gecemedi. O yedege GUVENME."
fi
exit "$TOPLAM_HATA"
