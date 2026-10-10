#!/bin/sh
# LGS backend'i icin dagitim sonrasi duman testi: temel akislar ayakta mi.
#
# Kullanim:  scripts/smoke-lgs.sh https://api-lgs.rehberim.xyz
#
# Hicbir sey YAZMAZ, yalniz okur. Uretimde calistirmak guvenlidir.
#
# YKS'nin smoke.sh'sinden ayri bir dosya: uclar farkli (giris ucu
# /api/auth/token/, /api/programs/ yok) ve iki urun ayri adreste.
set -u

API="${1:-https://api-lgs.rehberim.xyz}"
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

echo "Duman testi (LGS): $API"
echo

# Saglik ucu veritabanina da bakiyor; 200 ise PostgreSQL de ayakta.
kontrol 200 "/healthz"                "saglik ucu (+veritabani)"

# Kimliksiz erisim reddedilmeli. 200 gelirse izinler acilmis demektir.
kontrol 401 "/api/subjects/"          "kimliksiz istek reddediliyor"
kontrol 401 "/api/class-sections/"    "kimliksiz istek reddediliyor"
# Paketleme izni anonim istekte patlamamali: 403 ya da 500 degil, 401.
kontrol 401 "/api/exams/"             "paket izni anonimde 401 veriyor"

# Admin ayakta ve statik dosyalar servis ediliyor (WhiteNoise).
kontrol 200 "/admin/login/"           "admin aciliyor"

# Yanlis sifreyle giris 401 donmeli - 500 donerse bir sey bozuk.
# !! LGS'nin giris ucu /api/auth/token/ (SimpleJWT), YKS'deki /login/ degil.
gelen=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST \
    -H 'Content-Type: application/json' \
    -d '{"username":"__yok__","password":"__yok__"}' \
    "${API}/api/auth/token/")
if [ "$gelen" = "401" ]; then
    printf '  ✓ %-38s %s\n' "hatali giris 401 donuyor" "$gelen"
else
    printf '  ✗ %-38s %s (beklenen 401)\n' "hatali giris" "$gelen"
    hata=$((hata + 1))
fi

# Sifre sifirlama ucu ayakta mi. Kayitli olmayan bir adrese 200 donmeli
# (hesap sayimini engellemek icin yanit her kosulda ayni). 500 donerse
# e-posta ayari bozuk - orn. SMTP portu asili kaliyor.
gelen=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -X POST \
    -H 'Content-Type: application/json' \
    -d '{"email":"duman-testi@example.invalid"}' \
    "${API}/api/auth/password-reset/")
case "$gelen" in
    200) printf '  ✓ %-38s %s\n' "sifre sifirlama ucu" "$gelen" ;;
    429) printf '  ! %-38s %s (hiz siniri; biraz bekle)\n' "sifre sifirlama ucu" "$gelen" ;;
    *)   printf '  ✗ %-38s %s (beklenen 200)\n' "sifre sifirlama ucu" "$gelen"
         hata=$((hata + 1)) ;;
esac

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
    echo "$hata kontrol basarisiz. docs/lgs-railway.md ve docs/runbook.md'ye bak."
fi
exit "$hata"
