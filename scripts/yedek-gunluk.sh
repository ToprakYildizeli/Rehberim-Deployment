#!/bin/sh
# Gunluk otomatik yedek: iki urunu birden alir, saklama suresini uygular ve
# sonucu gunluge yazar. launchd bu betigi cagiriyor (bkz. docs/backup.md).
#
# Elle de calistirilabilir:  scripts/yedek-gunluk.sh
#
# Cikis kodu: kac urunun yedegi alinamadiysa o sayi. launchd bunu gunluge
# yaziyor; sifir olmayan bir kod "yedegim var" sanmanin tek panzehiri.
set -u

BURADA="$(cd "$(dirname "$0")" && pwd)"
REHBERIM="${REHBERIM_KOK:-$HOME/Desktop/Rehberim}"
export YEDEK_SAKLA="${YEDEK_SAKLA:-30}"

# Gun sonunda ne kadar yedek tutulacagi: 30 gun. Dosyalar ~200-400 KB, yani
# bir yillik yedek bile 150 MB'in altinda — sinirlayan sey disk degil,
# kisisel veriyi gereksiz uzun tutmamak (KVKK saklama ilkesi).

hata=0
al() {
    urun="$1"; dizin="$2"; port="$3"
    echo "=== $urun · $(date '+%Y-%m-%d %H:%M') ==="
    if [ ! -d "$REHBERIM/$dizin" ]; then
        echo "ATLANDI: $REHBERIM/$dizin yok"; hata=$((hata + 1)); return
    fi
    # Her urun ayri tunel portu: ikisi ust uste binerse ikincisi digerinin
    # veritabanina baglanir ve yanlis dokum alinir.
    if ( cd "$REHBERIM/$dizin" && YEDEK_PORT="$port" "$BURADA/yedek-al.sh" "$urun" ); then
        :
    else
        echo "BASARISIZ: $urun"; hata=$((hata + 1))
    fi
    echo
}

al yks Rehberim-Backend     55433
al lgs Rehberim-Backend-LGS 55432

if [ "$hata" -eq 0 ]; then
    echo "Gunluk yedek tamam."
else
    echo "UYARI: $hata urunun yedegi alinamadi."
    echo "Ilk bakilacak yer: railway oturumu suresi dolmus olabilir — 'railway whoami'."
fi
exit "$hata"
