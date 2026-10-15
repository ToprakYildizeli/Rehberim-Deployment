# Gunluk yedek isi: Railway'de cron olarak kosar, dokumu nesne depolamasina
# yazar. Kademe 2 (saglayicidan bagimsiz kopya) — bkz. ../docs/backup.md.
#
# Imaj bilerek kucuk ve dar: ic halka ne kadar az seyi calistiriyorsa, yedek
# isinin kendisi o kadar az sey kirabilir.
# !! Alpine surumu `postgresql18-client`'a gore secildi: 3.21 ve 3.22'de o
#    paket YOK (yalniz 17). 3.23 tam uretimdeki surumu veriyor (18.6).
#    Surumu dusurmek dokumu alinamaz hale getirir.
FROM alpine:3.23

# postgresql18-client: pg_dump SUNUCUDAN ESKI OLAMAZ. Uretimde PostgreSQL 18
#   calisiyor; 17 istemcisi dokumu hic alamaz ve hata mesaji bunu acikca
#   soylemez.
# rclone: S3 uyumlu her hedefe yaziyor (Cloudflare R2, Backblaze B2, S3).
# age: dokumu YUKLEMEDEN ONCE sifreler. Dosya ogrencilerin ve rehberlerin
#   tamamini iceriyor; kovanin disariya kapali olmasi tek basina yeterli bir
#   koruma degil.
RUN apk add --no-cache postgresql18-client rclone age tzdata ca-certificates

ENV TZ=Europe/Istanbul
COPY yedek.sh /usr/local/bin/yedek.sh
RUN chmod +x /usr/local/bin/yedek.sh

# Cron servisi: Railway konteyneri takvime gore ayaga kaldirir, is biter ve
# kapanir. Cikis kodu sifir degilse Railway dagitimi "crashed" gosteriyor —
# sessiz basarisizligin ilk gorunur oldugu yer burasi.
CMD ["/usr/local/bin/yedek.sh"]
