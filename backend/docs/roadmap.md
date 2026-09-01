# Rehberim — Yol Haritası

> **Kaynak:** Hoca geri bildirimi (`Rehberim Issues.pdf`, 22 Ağustos 2026)
> **Kapsam:** Bu belge **rehber (koç) web arayüzü + backend** işlerini planlar.
> **Son güncelleme:** 29 Ağustos 2026

## Kapsam ayrımı — kim neyi yapıyor

| Alan | Sahip | Bu belgede |
|---|---|---|
| Backend (Django/DRF) — tüm uçlar, veri modeli, izinler | **Biz** | ✅ |
| Rehber web arayüzü (`rehberim_koc`, React) | **Biz** | ✅ |
| Öğrenci mobil arayüzü (`rehberim_ogrenci`, Flutter) | Yunus | ❌ |
| Veli mobil arayüzü (`rehberim_veli`, Flutter) | Yunus | ❌ |

**Önemli ayrım:** Öğrenci ve veli *arayüzleri* Yunus'ta, ama onları besleyen
**backend uçları bizde**. Hocanın "Öğrenci Side" başlığı altında yazdığı maddelerin
bir kısmı aslında backend işi; onlar aşağıda **Faz E**'de toplandı.

---

## Nerede duruyoruz

**Bitmiş ve çalışır durumda:**

- Kimlik/rol: JWT auth, rol bazlı izinler, davet kodları (rehber→öğrenci, öğrenci→veli)
- Domain uçları: programlar + görevler, denemeler, hedefler, takvim, kitaplık,
  konu kataloğu ve konu ilerlemesi (1–5 seviye)
- Nesne bazlı yetkilendirme: rehber yalnız kendi öğrencileri, öğrenci kendi verisi,
  veli çocuğu salt-okunur
- Program şablonları + öğrenciye atama (`/api/program-templates/`, `/api/programs/assign/`)
- **Rutin** (tekrarlayan program): şablona öğrenci bağlanıp `auto_apply` açılınca yeni
  hafta açılışında görevler kendiliğinden materyalize olur. Rehber de öğrenci de kurabilir.
- Deneme netleri **doğru/yanlış** girişine geçti; net ve boş sunucuda türetiliyor
- Rehber web: Panel (gerçek veriden), Öğrenciler, Öğrenci detay (4 sekme), Takvim,
  Ders Programı (şablon + atama + rutin), davet kodu görünümü
- Profil düzenleme (`PATCH /api/auth/me/`)
- **A1 + A3** (22 Ağustos 2026): esnek program penceresi (`day_count`, örtüşme
  yasağı) ve blok türleri (`kind`, `exam_scope`, `counts_as_study`) — backend ve
  rehber web tamam.
- **A2 + A4/serbest süre** (23 Ağustos 2026): ders satırlı tahta görünümü
  (satırlar kullanıcı tarafından yönetiliyor, varsayılanı öğrencinin alanı) ve
  serbest dakika girişi (tahta 15 dk çözünürlüklü).
- **B3** (23 Ağustos 2026): panelde haftalık saat sınırı 80, yalnız çalışma +
  deneme blokları sayılıyor; pencere uzunluğuna göre normalize ediliyor.
- **A4 / süre hafızası** (23 Ağustos 2026): rehber × (ders, metod, konu) → son
  kullanılan süre; blok formunda varsayılan olarak geliyor. **Faz A tamamen bitti.**
- **C1** (23 Ağustos 2026): panelde AYT kıyaslaması alan (SAY/EA/SÖZ) seçtiriyor;
  ölçekler ve ders grupları alana göre, maksimumlar katalogdan.
- **B1** (25 Ağustos 2026): haftalık onay akışı — backend + rehber web. A1'in açık
  kenar durumu da kapandı (pencere daraltmak artık görev öksüz bırakmıyor).
- **B2** (25 Ağustos 2026): uyum yüzdesi **süre** üzerinden, haftalık özet +
  ay ay dağılım + zaman serisi grafiği. Panel de aynı sayıyı kullanıyor.
- **C2** (25 Ağustos 2026): takvimde etkinlikler nokta yerine kutu; hücre ve
  ajanda satırı taşmıyor.
- **E1 + E2** (26 Ağustos 2026): denemede kişisel/kurumsal ayrımı ve öğrenci
  çalışma istatistikleri ucu. İkisi de backend; arayüzleri Yunus'ta.
- **C3** (26 Ağustos 2026): Başarımlar — varsayılan set rehbere kopyalanıyor,
  rehber Ayarlar'dan düzenleyebilecek (uçlar hazır); öğrenci detayında yeni sekme.

**Testler:** backend 279/279 · `flutter analyze` temiz · web build + oxlint temiz

---

## Faz A — Ders Programı esnekliği

Hocanın geri bildiriminin en yoğun olduğu alan. Dördü de Ders Programı ekranını
ve `Task`/`WeeklyProgram` modellerini etkiliyor; birlikte planlanmalı.

### A1 · Esnek program penceresi — **backend ✅ · web ✅**

**Olması gereken:** Rehber hem **başlangıç gününü** hem **gün sayısını** seçebilmeli.
Örnek: Pazartesi program atayamadıysa, Salı günü "Pazartesiden Cumaya" 5 günlük bir
program yapabilmeli — yani başlangıç geçmiş bir tarih de olabilmeli.

**Varsayılan:** başlangıç = program atanmamış ilk gün, uzunluk = 7 gün. İkisi de
öğrenciye atamadan **hemen önce** Ders Programı ekranından değiştirilebilir.

**Backend'de yapıldı** (migration `0022`, kontrat `program-contract.md` v3):

- `WeeklyProgram.day_count` (1–31, varsayılan 7) eklendi; `end_date` artık
  `start_date + day_count - 1`. `start_date` geçmiş bir tarih olabilir.
- `unique_together = ('student', 'start_date')` **kaldırıldı**; yerine
  `WeeklyProgram.find_overlap()` ile **aralık örtüşme yasağı** geldi
  (karar: programlar örtüşemez). POST/PATCH/assign üçünde de `400`.
- Görev tarih doğrulaması pencereye göre genelleşti (`program.covers(date)`).
- `_next_free_start` yerine `WeeklyProgram.first_free_day()`; assign artık çakışan
  aralıkta sessizce +7 kaymıyor, `400` döndürüyor.
- weekday→tarih eşlemesi pencereye sığmayan günleri atlıyor (şablon + rutin).
- `/programs/current/` uzun pencereleri de buluyor (eski `today-6` filtresi kalktı).

**Web'de yapıldı:** Ders Programı'na pencere çubuğu (başlangıç + gün sayısı) eklendi;
tahta sütunları pencerenin gerçek tarihleri. Bloklar hafta günü yerine **pencere gün
indeksiyle** tutuluyor (7 günden uzun pencerede hafta günü tekrar ettiği için).
Şablonlar hafta gününe göre saklanmaya devam ediyor; çeviri iki yönlü ve pencereye
sığmayan bloklar kullanıcıya bildirilerek atlanıyor. Mevcut programın penceresi
değiştirilince PATCH'leniyor, örtüşme hatası ekranda gösteriliyor.

**Kabul:** Salı günü, geçmiş Pazartesiden başlayan 5 günlük bir program atanabiliyor;
tahta 5 sütun gösteriyor; görev doğrulaması bu pencereye göre çalışıyor.
*(Backend kısmı testli: `FlexibleProgramWindowTests`.)*

✅ **Kenar durum kapandı (25 Ağu 2026):** `day_count` küçültmek (ya da `start_date`
ileri kaydırmak) yeni pencerenin dışında görev bırakıyorsa `PATCH` artık `400`
döndürüyor (`{"day_count": [...]}`), kaç görev ve hangi günler olduğunu söyleyerek.
Görev eklemedeki `program.covers(date)` kuralının tersten delinmesi engellendi.
Web'de ayrı bir iş çıkmadı — pencere çubuğu hatayı zaten `apiMessage` ile basıyor.
*(Testli: 3 yeni test `FlexibleProgramWindowTests` içinde.)*

### A2 · İki tahta görünümü — **✅ (web)**

Butonla seçilen iki düzen: **saat satırlı** (mevcut) ve **ders satırlı** (satırlar
ders, sütunlar gün). Backend'in bilmesi gerekmedi — aynı `Task` verisi iki şekilde
çiziliyor, görünüm tercihi sunucuya yazılmıyor. `schedule_type` yalnız saatli/saatsiz
ayrımı için duruyor.

**Yapıldı:** Ders düzeninde saat serbest — bir hücreye bırakılan blok o günün ilk
boş dilimine yerleşiyor, satır değiştirmek bloğun dersini/türünü de değiştiriyor.
Dış meşguliyetler ve genel denemeler bir dersle eşleşmediğinden kendi satırlarını
alıyor (sıra: dersler → genel denemeler → dış meşguliyet).

**Satırlar kullanıcının:** yalnız programda blok bulunan dersler değil, istenen tüm
ders satırları açılabiliyor; kullanıcı satır ekleyip çıkarıyor. Varsayılan =
öğrencinin **alanına düşen** dersler (`GET /api/subjects/?student=&scope=field`,
kontrat v3.1; alan→AYT eşlemesi `Student.AYT_FIELD_SUBJECTS`). Blok taşıyan satır
gizlenemiyor. Tercih görünüm ayarı olduğu için sunucuya değil tarayıcıya yazılıyor.

**Kabul:** Aynı program iki görünümde de doğru çiziliyor, geçiş veri kaybetmiyor.

### A3 · Yeni blok türleri — **backend ✅ · web ✅**

**Olması gereken iki yeni blok:**

1. **Dış / günlük iş bloğu** — öğrencinin okul dersi, dershane, antrenman veya
   doktor randevusu gibi çalışma dışı meşguliyetleri. Programda yer kaplar ama
   **çalışma saatine sayılmaz** (bkz. B3).
2. **Genel TYT / AYT deneme bloğu** — şu an deneme eklenebiliyor ama blok
   oluştururken TYT seçilince ders soruluyor. "Genel" seçilebilmeli.

**Backend'de yapıldı** (migration `0022`, kontrat v3):

- `Task.kind` = `study` (varsayılan) / `external` / `exam`; `TemplateTask`'ta da var,
  şablon ve rutin blok türünü taşıyor.
- `Task.exam_scope` = `tyt` / `ayt` — genel deneme bloğu **ders seçmeden** kurulur.
  Karar: Subject kataloğuna sahte "Genel TYT" satırı eklenmedi, ayrı alan kullanıldı
  (katalog konu/kitap/net eşlemelerinde temiz kalsın diye).
- Salt-okunur `Task.counts_as_study` (= `kind != external`) — B3'ün saat hesabı
  bunu kullanacak.
- Alan kuralları `validate_block_kind()` içinde, Task ve TemplateTask ortak:
  dış blok ders/metod/kitap taşımaz ve başlık ister; deneme bloğu ders **ya da**
  kapsam ister (ikisi birden değil).
- Dış bloklar saat çakışma kontrolüne **dahil** — okuldayken çalışma bloğu konamaz.

**Web'de yapıldı:** Blok Oluştur panelinde tür seçimi (Çalışma / Dış / Deneme).
Dış blokta yalnız ad isteniyor, deneme bloğu ders seçmeden genel TYT/AYT olabiliyor.
Dış bloklar çizgili zeminle ayrışıyor; toplam saat yalnız çalışmayı sayıp dışı ayrı
gösteriyor, program ağırlığı özeti dış blokları tamamen dışarıda bırakıyor.

**Kabul:** Antrenman bloğu programda görünüyor ama haftalık çalışma saatine
eklenmiyor; ders seçmeden "Genel TYT Denemesi" bloğu oluşturulabiliyor.
*(Backend kısmı testli: `BlockKindTests`.)*

### A4 · Esnek süre + süre hafızası — **✅**

**Serbest süre yapıldı (web).** Süre artık sabit seçenek değil, dakika girişi
(5–720 dk) + sık kullanılan kısayollar. Tahtada bloklar saat cinsinden kesirli sayı
yerine **dakika** tutuyor (`startMin`/`durationMin`), böylece 3 × 20 dk tam 1 saat
ediyor. Tahtanın çözünürlüğü 15 dk'ya indi (saat hücresi dört bırakma dilimi);
"güne ekle" mevcut blokların bitişine yaslanarak sıkı yerleştiriyor.
**Backend'de değişiklik gerekmedi** — `duration_minutes` zaten dakika tutuyor ve
çakışma kontrolü dakika hassasiyetinde; 09:00/09:20/09:40'a üç 20 dk'lık blok
canlı olarak doğrulandı.

**Süre hafızası yapıldı** (migration `0023`, kontrat `program-contract.md` v3.2).
`BlockDurationDefault` = rehber × (ders, metod, konu) → son kullanılan süre.
İstenen iki kritik ayrıntı da karşılandı: hafıza **rehber özelinde** (öğrenci başına
satır açılmaz) ve **konu kombinasyonuna özel** ("Matematik denemesi" ile "Matematik
test" ayrı satırlar).

- Konu, `Task.title` metnidir (web'de `/api/topics/` kataloğundan seçilir); konusuz
  blok da kendi kombinasyonudur, o yüzden `topic` boş metin olabilir ama NULL olamaz —
  böylece tekillik kısıtı SQLite'ta da gerçekten uygulanır.
- **Yazma ucu yok:** hafıza görev `POST`/`PATCH` edilirken sessizce güncellenir
  (`TaskSerializer._remember_duration`). Yalnız rehber yazar — öğrenci kendi görevini
  kaydettiğinde hocanın varsayılanları değişmez. Ders/metodu olmayan bloklar (dış
  meşguliyet, genel deneme) hatırlanmaz.
- **Okuma:** `GET /api/block-durations/` (yalnız rehber, kendi hafızası). Web sayfa
  açılışında bir kez çekip harita kurar; ders/metod/konu değişince süre alanını doldurur,
  kombinasyon değişmedikçe elle girilen süreyi ezmez.
- **Taşımak hafızayı bozmaz** (23 Ağu 2026'da düzeltildi): `PATCH` yalnızca blok tanımı
  `(ders, metod, konu, süre)` değiştiyse yazar. İlk sürümde her `PATCH` yazıyordu ve
  eski bir bloğu sürüklemek, o kombinasyon için yeni girilmiş süreyi geri alıyordu.

**Kabul (canlı doğrulandı):** Ali'ye "TYT Türkçe · Test · Paragraf = 20 dk" kurulduktan
sonra Zeynep'in blok formunda aynı kombinasyon **20 dk** varsayılanıyla açılıyor.
"TYT Matematik · Deneme" 60 dk ile "TYT Matematik · Test" 25 dk ayrı satırlarda duruyor;
"TYT Türkçe · Test · Sözcükte Anlam" etkilenmiyor.
*(Testli: `BlockDurationMemoryTests`, 13 test.)*

---

## Faz B — Ölçüm ve onay

### B1 · Haftalık onay akışı — **✅ (backend + web)**

Hocanın en çok yer ayırdığı madde; ürünün güven modelini değiştiriyor.

**Akış:** Hafta bitince rehber, öğrencinin "tamamladım" dediği görev ve kitapları
haftalık toplantıda kontrol eder. Bir **onay butonu** ile "evet, dediklerini yapmış"
der. Onaylamadan önce düzenleyebilir — bir görevi "bitmemiş" işaretleyebilir ve
**uyum yüzdesi buna göre değişir**.

**Görünürlük kuralları:**
- Onaylanan program **veliye ve öğrenciye** görünür.
- **Veliye onaylanmamış hiçbir program gösterilmez.**
- Öğrenciye bildirim gitmez. Öğrenci "tamamlandı" işaretledikten sonra onun işi biter;
  gerisi rehberin onayıdır.

**Yapıldı (25 Ağustos 2026)** — migration `0024`, kontrat `program-contract.md` v3.3.

**Backend:** `WeeklyProgram.approved_at` + `approved_by`; salt-okunur `is_approved`
ve `is_finished` serileşiyor. Yeni uç `POST/DELETE /api/programs/{id}/approve/`
(ikisi de idempotent, program objesi döner).

Kullanıcının verdiği iki karar:
- **Onay ancak pencere kapandıktan sonra** verilebilir (`end_date < bugün`).
  Son günü bugün olan program henüz onaylanamaz → `400`. "Hafta bitince onaylanır"
  kuralını backend zorluyor.
- **Onay bir mühürdür:** onaydan sonra öğrenci o programın görevlerine yazamaz
  (`is_completed`, ekleme, silme, taşıma → `403`); okumaya devam eder. Böylece
  uyum yüzdesi (B2) onay sonrası kaymaz. **Rehber düzenlemeye devam edebilir** —
  yanlış işareti düzeltmek onun yetkisi, onay otomatik düşmez. Onay geri alınırsa
  öğrencinin yazma yetkisi geri gelir.

**Veli:** `GET /api/programs/` artık veli için de çalışıyor — ama yalnız
onaylanmışları döndürüyor; onaysız program listede de tekil `GET`'te de yok
(`403`). Veli her koşulda salt-okur.

**Web:** öğrenci detayı → Ders Programı sekmesinde onay çubuğu (durum rozeti,
`n/m görev · %x`, onaylayan + tarih) ve tahtada bloklar tıklanabilir —
rehber onaydan önce her bloğu yapıldı/yapılmadı olarak düzeltir. Onaylı programda
tahta kilitli görünür ve hafta seçicide "• Onaylı" yazar.

**Kabul (canlı doğrulandı, 8 senaryo):** veli onaysız programı ne listede ne tekil
`GET`'te görüyor (`0` kayıt / `403`) · devam eden program `400` ile reddediliyor
("Program 2026-08-27 tarihinde bitiyor…") · bitmiş program onaylanıyor
(`is_approved: true`, onaylayan "Selin Aydın") · onay sonrası öğrenci `403`, rehber
`200` alıyor · veli onaydan sonra `200` görüyor ama yazması `403` · onay geri
alınınca veli tekrar `403`, öğrenci tekrar `200`.
*(Testli: `WeeklyApprovalTests`, 18 test.)*

- **Yunus:** veli ve öğrenci tarafındaki gösterim (bizim kapsamımız dışında).
  Öğrenci app'inin onaylı programda `403` alacağını bilmesi gerekiyor — kilidi
  arayüzde göstermeli.

### B2 · Program uyum yüzdesi ve haftalık istatistik — **✅ (backend + web)**

**Olması gereken:** Öğrenciler sekmesinden bir öğrenci seçilip açılan **Ders Programı**
sekmesinde, **her haftanın altında** o programa dair özet:

- o programa yüzde kaç uyduğu
- kaç saat çalıştığı
- uzun vadeli istatistikler: "6 aydır kullanıyorsa bu programı yüzde kaçı ay ay
  tutturmuş" gibi
- uyum yüzdesinin **zaman içindeki grafiği**

**Yapıldı (25 Ağustos 2026)** — model değişikliği **yok**, kontrat
`program-contract.md` v3.4.

**Hesap — kullanıcının kararı: uyum SÜRE üzerinden.**
`percent = tamamlanan blokların dakikası / tüm blokların dakikası`. Görev sayısı
değil süre sayılır; 20 dk'lık bir tekrar ile 3 saatlik bir deneme aynı ağırlıkta
olmamalı. Paydaya yalnız `counts_as_study` bloklar girer — dış meşguliyet hariç,
**denemeler dahil**; B3'ün haftalık saat hesabıyla bilerek aynı küme, iki sayı
birbirini tutsun diye. Saatsiz programda süre olmadığı için görev sayısına düşülür
ve `basis` (`duration`/`count`/`empty`) hangisi olduğunu söyler.

**Backend:** `WeeklyProgram.compliance()` + program objesinde salt-okunur
`compliance`. Yeni uç `GET /api/programs/compliance/?student=<id>` üç parça döner:
`programs` (bitmiş haftaların zaman serisi), `months` (ay ay), `overall`.

İki tasarım kararı:
- **Seri yalnız bitmiş programlardan** — devam eden hafta kısmi kalır, grafiği
  yanıltır. Onun anlık yüzdesi zaten program objesinde var.
- **`months`/`overall` yalnız ONAYLI haftalardan.** Onay B1'de "gerçekten
  yapılmış" beyanıdır; onaysız haftanın beyanı doğrulanmamıştır ve uzun vadeli
  istatistiği kirletmemeli. Kaçının beklediği `pending_approval` ile söylenir;
  onaysız haftalar seride yine görünür.
- Yüzdeler **dakika ağırlıklı** (haftaların yüzdelerinin ortalaması değil), yoksa
  1 saatlik hafta ile 30 saatlik hafta aynı ağırlıkta sayılırdı.

**Web:** öğrenci detayı → Ders Programı sekmesine "Uyum Geçmişi" kartı: genel uyum /
planlanan / tamamlanan / onay bekleyen kutuları, **haftalık uyum çizgisi** (tek seri,
onaysız haftalar içi boş nokta ile ayrışır — renk tek başına anlam taşımıyor) ve
**ay ay uyum** çubukları. Onay çubuğundaki yüzde de artık sunucudan geliyor.
**Panel** de `dashboard.js` içindeki görev-sayısı hesabını bırakıp sunucunun
`compliance.percent` değerini kullanıyor — panel ile öğrenci sayfası artık aynı
sayıyı gösteriyor.

**Kabul (canlı doğrulandı):** Ali'ye 8 haftalık geçmiş kurulduğunda genel %76
(7 onaylı hafta, 37 sa planlanan / 28 sa tamamlanan), onay bekleyen 1 hafta
ortalamalara girmiyor ama seride görünüyor · 90 dk'lık antrenman bloğu hiçbir
toplama girmiyor · Temmuz %71 çıkıyor (yüzde ortalaması %70 olurdu — dakika
ağırlıklı çalışıyor) · tahtada bir bloğu yapıldı işaretlemek çubuğu
%75 → %100 (3 sa/4 sa → 4 sa/4 sa) yapıyor, geri almak eski hâline döndürüyor ·
açık ve koyu temada grafik okunur.
*(Testli: `ComplianceTests`, 19 test.)*

**Bağımlılık:** B1 (onay) ve A3 (blok türü — hangi blokların sayılacağı).

### B3 · Panel haftalık saat hedefi — **✅ (web)**

Üst sınır **40 → 80** çıkarıldı ve saat artık **yalnızca çalışma + deneme
bloklarını** sayıyor; A3'ün dış blokları (okul, antrenman, doktor) toplamın
dışında. **Backend'de değişiklik gerekmedi** — `Task.counts_as_study` zaten
serileşiyor, panel onu süzüyor (`rehberim_koc/src/api/dashboard.js`).

Esnek pencereye (A1) iki uyum daha: program toplamı **haftalık hıza** çevriliyor
(4 günlük program yapan öğrenci az çalışıyor görünmesin) ve "bu haftaki program"
tespiti sabit `+6 gün` yerine sunucudan gelen `end_date`'i kullanıyor.

**Kabul (canlı doğrulandı):** Ali Yılmaz'a 3 saatlik antrenman bloğu eklenince
haftalık saat 11,0 → **10,0** (eski hesap 11,0 gösteriyordu). Aynı programın
penceresi 7 → 4 güne çekilince 10,0 sa **17,5 sa/hafta** olarak raporlanıyor.

---

## Faz C — Panel ve raporlama düzeltmeleri

### C1 · Net değişimi tablosu: TYT/AYT ayrımı — **✅ (web)**

**Yapıldı (23 Ağustos 2026).** Öğrenci Kıyaslama kartında AYT seçilince **alan da
seçiliyor** (Sayısal / Eşit Ağırlık / Sözel) ve kıyas o alanla sınırlanıyor:

- Seçilen alan bir **süzgeç değil, ölçektir**: herkes o alanın ders kümesiyle
  hesaplanıp listelenir. Sayısalcının 40 mat + 30 fen neti Sayısal ölçeğinde 70,
  EA ölçeğinde 40'tır — ikisi de anlamlı, ikisi de kıyaslanabilir. Eskiden tek bir
  alansız ölçek vardı; "90/80" bundan çıkıyordu.
- Ders grupları ve maksimumları alana göre kuruluyor: EA'da Tarih **/10** (yalnız
  Tarih-1) ve Coğrafya **/6**, Sözel'de Tarih /21 ve Coğrafya /17.
- Maksimum netler artık frontend'de yazılı değil, `/api/subjects/` alanındaki
  `question_count` toplanarak çıkıyor. Bu sırada Sözel'de hiç görünmeyen
  **Din Kültürü** grubu da eklendi (6 net).
- "Toplam" artık ham `total_net` değil, öğrencinin **kendi alan derslerinin**
  toplamı — alan dışı bir net girilse bile 80 aşılamıyor.
- Backend'de değişiklik gerekmedi; alan→ders eşlemesi `Student.AYT_FIELD_SUBJECTS`in
  frontend'deki yansıması (o eşlemenin genel bir ucu yok, yalnız öğrenci bazlı
  `?student=&scope=field` var).

**Not:** "Net değişimi" listesi zaten sınav türüne duyarlıydı — son deneme, **aynı
türdeki** bir öncekiyle karşılaştırılıyor. Eksik olan kıyaslama kartıydı.

### C2 · Takvim arayüz düzeltmeleri — **✅ (web)**

**Olması gereken:** etkinlikler **tam kutu şeklinde** olacak ve hücreden **aşağı
taşmayacak**.

**Yapıldı (25 Ağustos 2026).** Backend'de değişiklik gerekmedi.

Ay ızgarasında etkinlikler **renkli nokta** olarak çiziliyordu ve fazlası
`slice(0, 3)` ile **sessizce düşüyordu** — 5 etkinlikli bir günde 2'sinin var
olduğu hiçbir yerde belli olmuyordu. Artık:

- Gün hücresi görünür bir **kutu** (kenarlık + yüzey); ayın dışındaki boşluklar
  kutu görünümü almıyor.
- Etkinlikler **adı okunan kutucuklar**: kategori rengiyle sol şerit, saat ve
  öğrenci adı (adı sığmazsa üç noktayla kırpılıyor, tam metin `title`'da).
- Hücre yüksekliği sabit (`min-height` + `overflow: hidden`) ve sığmayan
  etkinlikler **"+N daha"** ile sayılıyor — artık ne taşma var ne sessiz kayıp.
  Kutu sayısı `CHIPS_PER_CELL` sabitiyle hücre yüksekliğine bağlı, ikisi birlikte
  değişmeli.

**Ajanda satırındaki taşma da giderildi** (aynı ekranın ikinci kusuru): satır
`grid-template-columns: auto auto minmax(0,1fr) auto auto` ile kuruluydu ve
etkinlik adı **rozete** basılıyordu. `category` aslında backend'in serbest metin
`title`'ıdır (`CalendarEvent`'ta ayrı kategori alanı yok, `appointments.js`
`title`'ı `category`'ye eşliyor); uzun bir başlık rozeti 249 px'e şişirip satırı
**karttan 64 px dışarı** taşırıyor, öğrenci adı sütununu 0 px'e eziyordu. Ayrıca
öğrencisiz etkinlikte bir çocuk eksik render edildiği için metin yanlış sütuna
düşüyor ve hiç daralmıyordu. Satır artık **flex**: başlık ana satır, "öğrenci ·
not" ikinci satır, yalnız metin sütunu daralıyor.

**Kabul (canlı ölçüldü):** 5 etkinlikli günde ajandanın beş satırı da kartın
içinde (`right: 1451` ≤ `1476`), öğrencisiz etkinlik dahil · 31 gün hücresinin
**hiçbirinde** `scrollHeight > clientHeight` yok · 900 px genişlikte de taşma ve
yatay kaydırma yok · açık ve koyu temada temiz, konsol hatasız.

### C3 · Başarımlar sekmesi — **✅ (backend + web)**

**Yapıldı (26 Ağustos 2026)** — migration `0026` + veri migration'ı `0027`,
kontrat `achievements-contract.md` v1.

**Kullanıcının kararı: varsayılanlar hazır gelsin, rehber ileride Ayarlar'dan
ekleyip çıkarabilsin.** Bu yüzden başarım global bir katalog değil, **rehbere ait**
satırlar: yeni rehber kaydolunca varsayılan set kendisine **kopyalanıyor**
(`Rehberim.signals.seed_counselor_achievements`), mevcut rehberler veri
migration'ıyla yakalandı. Sonrasında sildiği/eklediği/değiştirdiği hiçbir şey
başka rehberi etkilemiyor.

**Varsayılan 12 başarım:** TYT 60 · 80 · 90 · 100 · 110 net · konu tamamlama
%25/%50/%75/%100 · program uyumu %60/%80/%100.

**Ölçütler:** `exam_net` (o türdeki denemelerin **en yüksek** toplam neti —
başarım "bir kez ulaştı" demektir, sonraki kötü deneme geri almaz),
`topic_completion` (seviye 5 konular / öğrencinin kapsamındaki konular) ve
`compliance` (B2'nin onaylı hafta uyumu).

**Kazanım saklanmıyor, anlık hesaplanıyor** — eşik değişince ya da bir deneme
silinince kayıtla gerçek arasında tutarsızlık kalmasın diye. Ayrı bir
"kazanılmışlar" tablosu yok.

**Uçlar:** `GET/POST /api/achievements/` + `GET/PATCH/DELETE /api/achievements/{id}/`
(yalnız rehber, yalnız kendi tanımları — **Ayarlar ekranı bunlara bağlanacak**) ve
`GET /api/achievements/progress/?student=<id>` (rehber · öğrenci · veli).

**Web:** öğrenci detayına **Başarımlar** sekmesi — özet kutuları (kazanılan sayısı,
en iyi TYT/AYT net, konu tamamlama), "Kazanılanlar" ve eşiğe yakınlığa göre sıralı
"Sıradakiler" kartları. Kazanım renkle **değil** önce ikon ve "Kazanıldı"
etiketiyle ayrışıyor.

**Kabul (canlı doğrulandı):** `rehber_demo`'nun 12 tanımı var; Ali 4/12 kazanmış
(TYT 60/80/90 net ve Program Uyumu %60), en iyi TYT neti 91,75, konu tamamlama
6/286 (%2,1), uyum %75,7 · eşik değiştirmek öğrencinin durumunu anında
değiştiriyor · bir rehberin sildiği varsayılan diğerini etkilemiyor.
*(Testli: `AchievementTests`, 25 test.)*

**Kalan:** Ayarlar ekranındaki düzenleme arayüzü (Faz D ile birlikte) ve öğrenci
tarafındaki kutlama (Yunus).

---

## Faz D — Ayarlar

Hocanın notu: *"Ayarlar bölümü tamamlanacak."* — ve doğrudan bize bırakılan bir
talimat var: **yapmadan önce kullanıcıya detayları sormak.**

Bu yüzden bu faz **bilerek boş bırakıldı**. Ayarlar'da tam olarak nelerin
bulunacağı (bildirim tercihleri? varsayılan program ayarları? kurum bilgisi?
davet kodu yenileme? tema?) netleşmeden kod yazılmayacak.

**Şimdiden bilinen iki madde:**

1. **Başarım düzenleme (C3).** Uçlar hazır (`GET/POST /api/achievements/`,
   `PATCH/DELETE /api/achievements/{id}/`) ve frontend sarmalayıcıları da yazıldı
   (`src/api/achievements.js`); eksik olan yalnızca Ayarlar'daki arayüz.
2. **Davet kodu yenileme.** Kod `Counselor.save()` içinde bir kez üretiliyor ve
   sabit kalıyor; sızması hâlinde yenileme yolu yok.

---

## Faz E — Yunus'un arayüzünü besleyen backend işleri

Arayüzler Yunus'ta; aşağıdaki **uçlar ve veri modeli bizde**.

### E1 · Deneme: kişisel / kurumsal ayrımı — **✅ (backend)**

**Yapıldı (26 Ağustos 2026)** — migration `0025`, kontrat `exam-contract.md` v1.1.

`ExamResult.source` = `personal` (varsayılan) / `institutional`. Kişisel = öğrenci
evde tek başına çözdü; kurumsal = kurum geneli, gözetimli ve herkesle aynı koşulda
sınav. Mevcut kayıtların tamamı `personal` olarak işaretlendi (canlı doğrulandı:
7 denemenin hepsi).

- `GET /api/exams/?source=personal|institutional` ile süzülüyor. **Bilinmeyen
  değer sessizce yok sayılıyor** — boş liste dönüp "veri kayboldu" izlenimi vermesin.
- Yanlış işaretlenmişse `PATCH` ile düzeltilebiliyor.
- Salt-okunur `ExamResult.is_institutional` yardımcı özelliği var.

**Yunus'a not:** deneme formuna bu seçimi eklemesi gerekiyor; göndermezse
`personal` kabul edilir, yani mevcut app kırılmaz.
*(Testli: `ExamSourceTests`, 6 test.)*

### E2 · Öğrenci istatistik uçları — **✅ (backend)**

**Yapıldı (26 Ağustos 2026)** — model değişikliği **yok**, kontrat
`program-contract.md` v3.5 §12. Uç: `GET /api/study-stats/?student=<id>`.

Döndürdüğü: `total_minutes`/`total_hours`, `by_category` (TYT/AYT/okul yüzdeleri)
ve `by_subject` (daire grafiği için ders dağılımı) — ikisi de çoktan aza sıralı.
`from`/`to` ile dönem daraltılabiliyor.

Kararlar:
- **Sayılan şey gerçekten yapılan çalışma**: `is_completed` **ve**
  `counts_as_study` bloklar. B2'nin uyum hesabıyla bilerek aynı küme.
- **Ders seçilmemiş genel deneme** bloğu kendi kapsamına (`tyt`/`ayt`) sayılıyor
  ama `by_subject`'e girmiyor (dersi yok).
- **Saatsiz programda süre yok**, o görevler dağılıma katılmıyor — toplam 0 döner,
  hata değil.
- **Veli yalnız onaylanmış programlardaki** çalışmayı görüyor (B1'in kuralı burada
  da geçerli).

**Kabul (canlı doğrulandı):** Ali için öğrenci ve rehber **31,0 sa** görüyor,
veli **28,0 sa** (onaysız hafta düşüyor — B2'deki 1680 dk ile birebir tutuyor);
rehber `student` vermezse `400`, başkasının öğrencisinde `404`.
*(Testli: `StudyStatsTests`, 14 test.)*

### E3 · Veli erişimi — **✅ (backend)**

**Yapıldı (29 Ağustos 2026)** — migration `accounts/0003`, kontrat
`auth-contract.md` **v2.0** (kırıcı, yalnız veli akışında).
Veli **arayüzü** hâlâ Yunus'ta; aşağısı onu besleyen backend'dir.

**Bağlanma akışı değişti.** Veli artık öğrencinin `connect_code`'unu değil,
**öğrencinin id'si + o öğrencinin rehberinin davet kodunu** giriyor:

```
POST /api/parents/connect-student/   → { "student": 3, "counselor_code": "AB12CD" }
POST /api/auth/register/parent/      → aynı ikili, opsiyonel (ikisi birlikte)
```

- Rehbere bağlı **olmayan** öğrenciye veli bağlanamaz (ikili doğrulanır).
- Hata mesajı **tek ve ayrımsız**: "öğrenci yok" ile "kod yanlış" ayrı ayrı
  söylenmiyor — yoksa kodu bilen biri id deneyerek rehberin öğrenci listesini
  çıkarabilirdi.
- `Student.connect_code` alanı modelde duruyor ama **artık hiçbir akışta
  kullanılmıyor**; ileride kaldırılabilir.

**Davet kodu artık gerçekten değişmez.** Önceden yalnızca boşsa üretiliyordu ama
sonradan değiştirilmesini engelleyen bir şey yoktu. Şimdi:

- `Counselor.invite_code` → `editable=False`; `save()` diskteki değerle
  karşılaştırıp değişikliği `ValueError` ile reddediyor (boşaltma dahil).
- Üretim `save_with_unique_code()` ile yapılıyor: "önce bak sonra yaz" yarışında
  iki kayıt aynı kodu alırsa `IntegrityError` yakalanıp yeni kodla deneniyor.
  Asıl güvence yine veritabanındaki `unique=True`.
- Aynı sağlamlaştırma `Student.connect_code` için de geçerli.

**Velinin gördüğü (kullanıcı kararı, 29 Ağu 2026):**

| Veri | Uç | Durum |
|---|---|---|
| Denemeler, ders kırılımıyla ("Türkçe 6D 1Y") | `GET /api/exams/` + `/{id}/` | ✅ **yeni açıldı** |
| Haftalık programlar — **yalnız onaylı** | `GET /api/programs/?student=` | ✅ (B1'den) |
| Uyum yüzdeleri — **yalnız onaylı** | `GET /api/programs/compliance/?student=` | ✅ (B2'den) |
| Haftalık toplam çalışma saati | `compliance` → `completed_hours` · `GET /api/study-stats/` | ✅ **alan eklendi** |
| Konu takip listesi | `GET /api/topic-progress/?student=` | ✅ (salt-okur) |
| Takvim / toplantılar | `GET /api/calendar/` | ✅ (açık bırakıldı) |
| **Kitaplık** | `/api/books/`, `/api/book-topics/` | ❌ **kapatıldı** |
| **Hedefler** | `/api/goals/` | ❌ **kapatıldı** |

- Denemede **onay şartı yok** — deneme programa bağlı değil, öğrencinin doğrudan
  girdiği bir sonuç. Program tarafındaki "yalnız onaylı" kuralı orada geçmez.
- `compliance` objesine `completed_hours` eklendi: `study_hours` **planlanan**,
  `completed_hours` **gerçekten çalışılan** saat. Veli ekranı ikincisini kullanır.
- Birden çok çocuğu olan veli programları ve konu takibini `?student=` ile
  daraltabiliyor (denemelerde zaten vardı).
- Veli her yerde **salt-okurdur**; yazma denemesi `403`.

**Bilinen sınır (kullanıcı kararı):** davet kodu bir rehberin tüm öğrencileri için
aynı olduğundan, kodu bilen bir veli id deneyerek aynı rehberin başka bir
öğrencisine de bağlanabilir. Bilinçli kabul edildi; sertleştirmek gerekirse
öğrenci soyadı üçüncü alan olarak eklenir (hocanın PDF'teki tavsiyesi buydu).

**Yunus'a not:** veli app'i `connect_code` yerine `student` + `counselor_code`
göndermeli; kitaplık ve hedefler veli ekranında yer almayacak.

*(Testli: `ParentAccessTests` 16 · `ParentConnectTests` 7 · `ParentRegisterLinkTests` 4 ·
`InviteCodeTests` 6.)*

---

## Kapsam dışı (karar verildi)

- **Deneme foto / OCR aktarımı** — yapılmayacak.
- **Üretim sertleştirmesi** (`SECRET_KEY` env'e, `DEBUG=False`, PostgreSQL,
  `tr` / `Europe/Istanbul`) — şimdilik kapsam dışı, lokal geliştirme yeterli.
  Gerçek bir sunucu hedefi çıkarsa bu liste hazır.
- **İngilizce ders konuları** seed'e girmeyecek.

---

## Öneri sıra

1. ~~**A1 + A3**~~ — **bitti** (backend migration `0022` + rehber web).
2. ~~**A4**, sonra **A2**~~ — **bitti**. Faz A'da açık madde kalmadı.
3. ~~**B3**~~, ~~**B1**~~, ~~**B2**~~ — **bitti**. Faz B'de açık madde kalmadı.
4. ~~**C1**~~, ~~**C2**~~, ~~**C3**~~ — **bitti**. Faz C'de açık madde kalmadı.
5. ~~**E1 / E2**~~, ~~**E3**~~ — **bitti**. Faz E'de açık madde kalmadı
   (veli *arayüzü* Yunus'ta).
6. **D** — detaylar netleşince. **Tek kalan faz.**

## Açık sorular

1. **Ayarlar'da ne olacak?** (Faz D — hocanın açık talimatı: sormadan yapma)
2. ~~**Esnek programda çakışma**~~ — **karar verildi (22 Ağu 2026): örtüşme
   engellenecek.** Aynı öğrencinin iki programının tarih aralığı kesişemez; ihlal
   `400` döner. Gerekçe: `/programs/current/` tek program döndürebilsin, uyum
   yüzdesi (B2) hangi görevin hangi programa sayıldığını çözmek zorunda kalmasın,
   rutin aynı güne iki kez yazmasın.
3. ~~**Veli tam olarak neyi görecek?**~~ — **karar verildi (29 Ağu 2026):**
   denemeler (ders kırılımıyla) · onaylı programlar + uyum · konu takip listesi ·
   haftalık çalışma saati · takvim. **Kitaplık ve hedefler veliye kapalı.**
   Bağlanma: öğrenci id'si + rehberin davet kodu.
4. ~~**Uyum yüzdesi nasıl hesaplanacak?**~~ — **karar verildi (25 Ağu 2026):
   süre üzerinden**, `counts_as_study` bloklar (dış hariç, denemeler dahil);
   dönemsel ortalamalar dakika ağırlıklı ve yalnız onaylı haftalardan.
