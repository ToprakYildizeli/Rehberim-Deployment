#!/bin/sh
# Dagitim sonrasi duman testi: temel akislar ayakta mi.
#
# Kullanim:  scripts/smoke.sh https://api.rehberim.xyz
#
# Hicbir sey YAZMAZ, yalniz okur. Uretimde calistirmak guvenlidir.
set -u

API="${1:-https://api.rehberim.xyz}"
hata=0

kontrol() {
    beklenen="$1"; yol="$2"; aciklama="$3"
    gelen=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "${API}${yol}")
    if [ "$gelen" = "$beklenen" ]; then
        printf '  ✓ %-38s %s\n' "$aciklama" "$gelen"
    else
        printf '  ✗ %-38s %s (beklenen %s)\n' "$aciklama" "$gelen" "$beklenen"
        hata=$((hata + 1))
    fi
}

echo "Duman testi: $API"
echo

# Saglik ucu veritabanina da bakiyor; 200 ise PostgreSQL de ayakta.
kontrol 200 "/healthz"                "saglik ucu (+veritabani)"

# Kimliksiz erisim reddedilmeli. 200 gelirse izinler acilmis demektir.
kontrol 401 "/api/subjects/"          "kimliksiz istek reddediliyor"
kontrol 401 "/api/programs/"          "kimliksiz istek reddediliyor"

# Admin ayakta ve statik dosyalar servis ediliyor (WhiteNoise).
kontrol 200 "/admin/login/"           "admin acilyor"

# Yanlis sifreyle giris 401 donmeli - 500 donerse bir sey bozuk.
gelen=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST \
    -H 'Content-Type: application/json' \
    -d '{"username":"__yok__","password":"__yok__"}' \
    "${API}/api/auth/login/")
if [ "$gelen" = "401" ]; then
    printf '  ✓ %-38s %s\n' "hatali giris 401 donuyor" "$gelen"
else
    printf '  ✗ %-38s %s (beklenen 401)\n' "hatali giris" "$gelen"
    hata=$((hata + 1))
fi

# Admin sayfasindaki ozetli CSS gercekten servis ediliyor mu.
css=$(curl -s --max-time 15 "${API}/admin/login/" \
      | grep -o '/static/admin/css/[^"]*base[^"]*css' | head -1)
if [ -n "$css" ]; then
    kontrol 200 "$css"                "statik dosya (WhiteNoise)"
else
    printf '  ✗ %-38s CSS adresi bulunamadi\n' "statik dosya"
    hata=$((hata + 1))
fi

# HTTPS yonlendirmesi: duz HTTP kalici yonlendirme dondurmeli.
duz=$(printf '%s' "$API" | sed 's|^https://|http://|')
gelen=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "${duz}/healthz")
case "$gelen" in
    301|302|307|308) printf '  ✓ %-38s %s\n' "HTTP -> HTTPS yonlendirmesi" "$gelen" ;;
    *) printf '  ! %-38s %s (yonlendirme beklenirdi)\n' "HTTP -> HTTPS" "$gelen" ;;
esac

echo
if [ "$hata" -eq 0 ]; then
    echo "Hepsi gecti."
else
    echo "$hata kontrol basarisiz. docs/runbook.md'ye bak."
fi
exit "$hata"
