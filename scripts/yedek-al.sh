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
#   YEDEK_SAKLA   kac gunluk yedek tutulacak (varsayilan 0 = hicbir sey silinmez)
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
SAKLA="${YEDEK_SAKLA:-0}"
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
DOSYA="$DIZIN/$URUN-$PROJE-$(date +%Y%m%d-%H%M).dump"
PGPASSWORD="$PGPASS_" "$PG_DUMP" -h 127.0.0.1 -p "$PORT" -U "$PGUSER_" -d "$PGDB_" \
    --format=custom --file="$DOSYA"
chmod 600 "$DOSYA"   # kisisel veri; baska kullaniciya okutma

# --- 6. Yedek gercekten okunabiliyor mu -------------------------------------
# Bos ya da yarim yazilmis bir dosya da "yedek" gorunur. Icindekiler
# listelenemiyorsa yedek yoktur.
NESNE="$("$PG_RESTORE" --list "$DOSYA" 2>/dev/null | grep -c '^[0-9]' || true)"
[ "${NESNE:-0}" -gt 0 ] || { echo "DOGRULAMA BASARISIZ: dosya okunamiyor ($DOSYA)" >&2; exit 1; }

# Satir sayilari: sema dogru olup verinin BOS gelmesi mumkun, ve bu sessiz
# bir ariza olurdu. Sayilar uretimden okunup dokumun yanina yaziliyor;
# `yedek-prova.sh` geri yukledigi veritabanini bu dosyayla karsilastiriyor.
#
# `n_live_tup` istatistik tablosundan geliyor ve YAKLASIKTIR (autovacuum
# guncelliyor). Provada birebir esitlik beklenmesin diye gercek sayimi
# `count(*)` ile aliyoruz; tablo sayisi az, maliyeti onemsiz.
PSQL="$(dirname "$PG_DUMP")/psql"
SAYIM_DOSYA="$DOSYA.sayim"
PGPASSWORD="$PGPASS_" "$PSQL" -h 127.0.0.1 -p "$PORT" -U "$PGUSER_" -d "$PGDB_" -tAq <<'SQL' \
    | sed '/^$/d' | sort > "$SAYIM_DOSYA"
select format('select %L as t, count(*) as n from %I.%I',
              c.relname, n.nspname, c.relname)
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where c.relkind = 'r' and n.nspname = 'public'
\gexec
SQL
# `\gexec` her tablo icin bir satir uretiyor: "tablo|sayi".
SAYIM="$(awk -F'|' '$2 > 0 {print $1 "=" $2}' "$SAYIM_DOSYA" | sort -t= -k2 -rn | head -6 \
    | awk '{printf "%s%s", ayir, $0; ayir=" · "} END {print ""}')"

# --- 7. Saklama (yalniz istenirse) -----------------------------------------
# Varsayilan 0: hicbir sey silinmez. Eski yedekleri kendiliginden silen bir
# betik, bir gun tek saglam yedegi de siler. Gun sayisi acikca verilmeli ve
# en az iki yedek her kosulda korunur.
if [ "$SAKLA" -gt 0 ]; then
    # En yeni IKI yedek her kosulda korunur (tarih ne olursa olsun); geri
    # kalanlardan $SAKLA gunden eski olanlar silinir. Betik uzun sure
    # calismadiysa elde hic yedek kalmamasin diye.
    ls -1t "$DIZIN/$URUN-"*.dump 2>/dev/null | tail -n +3 | while read -r gecmis; do
        if [ -n "$(find "$gecmis" -mtime "+$SAKLA" 2>/dev/null)" ]; then
            echo "  siliniyor (>$SAKLA gun): $(basename "$gecmis")"
            rm -f "$gecmis" "$gecmis.sayim"
        fi
    done
fi

TABLO="$(wc -l < "$SAYIM_DOSYA" | tr -d ' ')"
echo
echo "Yedek alindi: $DOSYA"
echo "  boyut   : $(du -h "$DOSYA" | cut -f1)"
echo "  nesne   : $NESNE"
echo "  tablo   : $TABLO (sayim: $(basename "$SAYIM_DOSYA"))"
echo "  satirlar: $SAYIM"
echo
echo "Provasi yapilmamis yedek, yedek sayilmaz:"
echo "  scripts/yedek-prova.sh $DOSYA"
