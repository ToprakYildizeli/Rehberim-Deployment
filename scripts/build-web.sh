#!/bin/sh
# Öğrenci ve veli uygulamalarını TARAYICI için derler ve tek bir klasörde
# toplar: <cikti>/ogrenci ve <cikti>/veli.
#
# Kullanım:
#   scripts/build-web.sh                       # üretim API'sine bakar
#   scripts/build-web.sh http://127.0.0.1:8000/api   # yerel backend
#   CIKTI=/tmp/web scripts/build-web.sh
#
# Neden tek klasör: iki uygulama tek alan adının altında iki yolda duruyor
# (app.rehberim.xyz/ogrenci, /veli). Bunun bedeli sıfır, kazancı üç yerde:
# tek DNS kaydı, tek CORS kökeni, tek dağıtım. İki alt alan adı kurmak üç
# şeyi de ikiye katlardı.
#
# ⚠️ Uygulamalar Yunus'un repo'larında ve **dal üzerinde** duruyor
# (`ogrenci-tamamlama`, `veli-app`). Derlemeden önce doğru dalda olduğunu
# doğrula; `main`'den derlersen bu iş için yazılan ekranların hiçbiri yok.
set -eu

API="${1:-https://api.rehberim.xyz/api}"
KOK="$(cd "$(dirname "$0")/../.." && pwd)"
CIKTI="${CIKTI:-$KOK/Rehberim-Deployment/build/web}"

OGRENCI="$KOK/Rehberim-Frontend-Ogrenci"
VELI="$KOK/Rehberim-Frontend-Veli"

# Öğrenci uygulaması adresin sonunda eğik çizgi bekliyor, veli beklemiyor.
# İkisi de kendi `ApiConfig`inde böyle yazılmış; burada uydurmuyoruz.
API_OGRENCI="$(printf '%s' "$API" | sed 's#/*$##')/"
API_VELI="$(printf '%s' "$API" | sed 's#/*$##')"

echo "API (öğrenci): $API_OGRENCI"
echo "API (veli)   : $API_VELI"
echo "Çıktı        : $CIKTI"
echo

for repo in "$OGRENCI" "$VELI"; do
    dal=$(git -C "$repo" rev-parse --abbrev-ref HEAD)
    echo "  $(basename "$repo"): dal '$dal'"
done
echo

echo "→ öğrenci derleniyor"
( cd "$OGRENCI" && flutter build web --release \
    --base-href /ogrenci/ \
    --dart-define=API_BASE_URL="$API_OGRENCI" >/dev/null )

echo "→ veli derleniyor"
( cd "$VELI" && flutter build web --release \
    --base-href /veli/ \
    --dart-define=API_BASE_URL="$API_VELI" >/dev/null )

rm -rf "$CIKTI"
mkdir -p "$CIKTI"
cp -R "$OGRENCI/build/web" "$CIKTI/ogrenci"
cp -R "$VELI/build/web" "$CIKTI/veli"

# Kök sayfa: iki uygulamaya giriş. Barındırma kökü boş kalmasın.
cat > "$CIKTI/index.html" <<'HTML'
<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rehberim</title>
<style>
  :root { color-scheme: light }
  body { font: 16px/1.6 system-ui, sans-serif; margin: 0; min-height: 100vh;
         display: grid; place-items: center; background: #eff1f6; color: #1a1c2c }
  main { width: min(28rem, 90vw) }
  h1 { font-size: 1.3rem; margin: 0 0 1.2rem }
  a { display: block; padding: 1rem 1.2rem; margin: .7rem 0; background: #fff;
      border-radius: 14px; text-decoration: none; color: inherit;
      box-shadow: 0 2px 10px rgba(0,0,0,.06) }
  small { color: #6b7080 }
</style>
<main>
  <h1>Rehberim</h1>
  <a href="/ogrenci/">Öğrenci uygulaması<br><small>Programın, denemelerin, konu takibin</small></a>
  <a href="/veli/">Veli uygulaması<br><small>Çocuğunuzun programı ve gelişimi</small></a>
</main>
HTML

# Derlenen paketin gerçekten doğru adresi taşıdığını doğrula. Yanlış adresle
# çıkmak sessiz bir arıza: sayfa açılır, giriş çalışmaz.
for uygulama in ogrenci veli; do
    if ! grep -q "$API_VELI" "$CIKTI/$uygulama/main.dart.js"; then
        echo "HATA: $uygulama paketinde '$API_VELI' geçmiyor." >&2
        exit 1
    fi
done

echo
echo "Hazır: $CIKTI"
du -sh "$CIKTI/ogrenci" "$CIKTI/veli"
