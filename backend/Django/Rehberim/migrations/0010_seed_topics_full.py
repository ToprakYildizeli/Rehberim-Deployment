from django.db import migrations


# Konu kataloğu — iki müfredat (kaynak: Konular.pdf ve Maarif Konular.pdf).
# Konular okul derslerine (category='okul') sınıf sınıf bağlanır.
# Felsefe 9 ve 12 her iki müfredatta da konusuzdur (bilerek boş).

ESKI = {
    "Türk Dili ve Edebiyatı": {
        "9": [
            "Giriş (Edebiyat Nedir, Metinlerin Sınıflandırılması, Dilin Kullanımından Doğan Türler)",
            "Hikaye (Olay ve Durum Hikayesi)",
            "Şiir (Şiir Bilgisi, Türleri, Ahenk Unsurları)",
            "Masal / Fabl",
            "Roman (Roman Türleri, Yapı Unsurları)",
            "Tiyatro (Geleneksel ve Modern Tiyatroya Giriş)",
            "Biyografi / Otobiyografi",
            "Mektup / E-Posta",
            "Günlük / Blog",
        ],
        "10": [
            "Giriş (Edebiyatın Tarihle ve Dinle İlişkisi, Türk Edebiyatının Dönemleri)",
            "Hikaye (Dede Korkut, Halk Hikayesi, Mesnevi, Tanzimat ve Milli Edebiyat Hikayesi)",
            "Şiir (İslamiyet Öncesi, Geçiş Dönemi, Halk Şiiri, Divan Şiiri)",
            "Destan / Efsane",
            "Roman (Tanzimat, Servet-i Fünun, Milli Edebiyat Dönemi Romanı)",
            "Tiyatro (Geleneksel Türk Tiyatrosu)",
            "Anı (Hatıra)",
            "Haber Metni",
            "Gezi Yazısı",
        ],
        "11": [
            "Giriş (Edebiyat ve Toplum İlişkisi, Edebiyatın Sanat Akımlarıyla İlişkisi)",
            "Hikaye (Cumhuriyet Dönemi Hikayesi - 1923-1960 / 1960 Sonrası)",
            "Şiir (Tanzimat, Servet-i Fünun, Fecr-i Ati, Milli Edebiyat ve Cumhuriyet Dönemi Şiiri)",
            "Makale",
            "Roman (Cumhuriyet Dönemi Romanı - 1923-1950 / 1950-1980)",
            "Tiyatro (Cumhuriyet Dönemi Tiyatrosu)",
            "Sohbet ve Fıkra",
            "Eleştiri",
            "Mülakat / Röportaj",
        ],
        "12": [
            "Giriş (Edebiyat ve Felsefe / Psikoloji İlişkisi, Dil Unsurları)",
            "Hikaye (1980 Sonrası Türk Hikayesi)",
            "Şiir (Cumhuriyet Sonrası Saf Şiir, Toplumcu Şiir, Garip, İkinci Yeni vb.)",
            "Roman (1980 Sonrası Türk Romanı, Dünya Edebiyatında Roman)",
            "Tiyatro (1980 Sonrası Türk Tiyatrosu, Dünya Edebiyatında Tiyatro)",
            "Deneme",
            "Söylev (Nutuk)",
        ],
    },
    "Matematik": {
        "9": [
            "Mantık",
            "Kümeler",
            "Denklem ve Eşitsizlikler (Gerçek Sayılar, Mutlak Değer, Oran-Orantı, Problemler)",
            "Üslü ve Köklü İfadeler",
            "Üçgenler (Açı, Eşlik, Benzerlik, Yardımcı Elemanlar, Alan, Trigonometriye Giriş)",
            "Veri (Merkezi Eğilim ve Yayılım Ölçüleri, Grafikler)",
        ],
        "10": [
            "Sayma ve Olasılık (Permütasyon, Kombinasyon, Binom, Olasılık)",
            "Fonksiyonlar (Fonksiyon Kavramı, Grafikler, Bileşke ve Ters Fonksiyon)",
            "Polinomlar ve Çarpanlara Ayrılma",
            "İkinci Dereceden Denklemler ve Karmaşık Sayılar",
            "Dörtgenler ve Çokgenler",
        ],
        "11": [
            "Trigonometri (Yönlü Açılar, Trigonometrik Fonksiyonlar, Teoremler, Grafikler)",
            "Analitik Geometri (Noktanın ve Doğrunun Analitiği)",
            "Fonksiyonlarda Uygulamalar (Parabol, Dönüşümler)",
            "İkinci Dereceden İki Bilinmeyenli Denklem ve Eşitsizlik Sistemleri",
            "Çember ve Daire",
            "Uzay Geometri (Katı Cisimler: Prizma, Piramit)",
            "Olasılık (Koşullu Olasılık, Deneysel ve Teorik Olasılık)",
        ],
        "12": [
            "Üstel ve Logaritmik Fonksiyonlar",
            "Diziler (Aritmetik ve Geometrik Dizi)",
            "Trigonometri (Toplam-Fark, Yarım Açı, Trigonometrik Denklemler)",
            "Dönüşümler Geometrisi",
            "Türev (Limit, Süreklilik, Anlık Değişim Oranı, Türev Kuralları ve Uygulamaları)",
            "İntegral (Belirsiz ve Belirli İntegral, Alan Hesabı)",
            "Çemberin Analitik İncelenmesi",
        ],
    },
    "Geometri": {
        "9": [
            "Doğruda ve Üçgende Açılar",
            "Üçgenlerde Eşlik ve Benzerlik",
            "Üçgenin Yardımcı Elemanları (Açıortay, Kenarortay, Yükseklik)",
            "Üçgen Eşitsizliği",
            "Dik Üçgen ve Trigonometri",
            "Üçgende Alan",
        ],
        "10": [
            "Çokgenler ve Düzgün Çokgenler",
            "Yamuk",
            "Paralelkenar ve Eşkenar Dörtgen",
            "Dikdörtgen ve Kare",
            "Deltoid",
            "Prizmalar ve Piramitler (Yüzey Alanı ve Hacim)",
        ],
        "11": [
            "Noktanın Analitik İncelenmesi",
            "Doğrunun Analitik İncelenmesi",
            "Çemberde Açılar ve Teğet Özellikleri",
            "Çemberde Uzunluk",
            "Dairenin Çevresi ve Alanı",
            "Küre ve Silindir (Yüzey Alanı ve Hacim)",
        ],
        "12": [
            "Öteleme, Dönme ve Simetri Dönüşümleri",
            "Çemberin Analitik Denklemi",
            "Koniler (Yüzey Alanı ve Hacim)",
        ],
    },
    "Fizik": {
        "9": [
            "Fizik Bilimine Giriş",
            "Madde ve Özellikleri (Özkütle, Dayanıklılık, Adezyon-Kohezyon)",
            "Hareket ve Kuvvet (Bir Boyutta Hareket, Newton'ın Hareket Yasaları)",
            "İş, Güç ve Enerji (Mekanik Enerji, Enerjinin Korunumu)",
            "Isı ve Sıcaklık (Genleşme, Hal Değişimi, Isı Aktarımı)",
            "Elektrostatik (Elektrik Yükleri, Elektroskop, Coulomb Yasası)",
        ],
        "10": [
            "Elektrik ve Magnetizma (Akım, Direnç, Potansiyel Farkı, Mıknatıslar ve Manyetik Alan)",
            "Basınç ve Kaldırma Kuvveti (Katı, Sıvı, Gaz Basıncı ve Arşimet İlkesi)",
            "Dalgalar (Yay, Su, Ses ve Işık Dalgaları)",
            "Optik (Aydınlanma, Gölge, Yansıma, Aynalar, Kırılma, Mercekler, Renk)",
        ],
        "11": [
            "Vektörler",
            "Bağıl Hareket",
            "Newton'ın Hareket Yasaları (Sürtünmeli Yüzeyler, İvmeli Hareket)",
            "Bir Boyutta ve İki Boyutta Sabit İvmeli Hareket (Atışlar)",
            "İş, Güç ve Enerji Korunumu",
            "İtme ve Çizgisel Momentum",
            "Tork, Denge ve Kütle/Ağırlık Merkezi",
            "Basit Makineler",
            "Elektriksel Kuvvet, Alan ve Potansiyel",
            "Düzgün Elektrik Alan ve Sığaçlar",
            "Manyetizma ve Elektromanyetik İndükleme",
            "Alternatif Akım ve Transformatörler",
        ],
        "12": [
            "Çembersel Hareket (Düzgün Çembersel Hareket, Virajlar, Dönerek Öteleme)",
            "Açısal Momentum",
            "Kütle Çekim Yasası ve Kepler Yasaları",
            "Basit Harmonik Hareket",
            "Dalga Mekaniği (Su Dalgalarında Kırınım ve Girişim, Doppler Olayı)",
            "Elektromanyetik Dalgalar",
            "Atom Fiziklerine Giriş ve Radyoaktivite",
            "Özel Görelilik",
            "Modern Fizik (Siyah Cisim Işıması, Fotoelektrik Olay, Compton Saçılması)",
            "Modern Fiziğin Teknolojideki Uygulamaları",
        ],
    },
    "Kimya": {
        "9": [
            "Kimya Bilimi (Simyadan Kimyaya, Kimya Disiplinleri, Güvenlik Sembolleri)",
            "Atom ve Periyodik Sistem (Atom Modelleri, Periyodik Cetvel ve Özellikleri)",
            "Kimyasal Türler Arası Etkileşimler (Güçlü ve Zayıf Etkileşimler)",
            "Maddenin Halleri (Katılar, Sıvılar, Gazlar, Plazma)",
            "Doğa ve Kimya (Su, Toprak ve Hava Kimyası)",
        ],
        "10": [
            "Kimyanın Temel Kanunları ve Kimyasal Hesaplamalar (Mol Kavramı, Tepkimeler)",
            "Karışımlar (Homojen-Heterojen Karışımlar, Ayırma ve Saflaştırma Yöntemleri)",
            "Asitler, Bazlar ve Tuzlar",
            "Kimya Her Yerde (Temizlik Maddeleri, Polimerler, İlaçlar, Gıdalar)",
        ],
        "11": [
            "Modern Atom Teorisi (Kuantum Sayıları, Elektron Dizilimleri, Periyodik Özellikler)",
            "Gazlar (Gaz Yasaları, İdeal Gaz Denklemi, Gerçek Gazlar)",
            "Sıvı Çözeltiler ve Çözünürlük (Derişim Birimleri, Koligatif Özellikler)",
            "Kimyasal Tepkimelerde Enerji (Endotermik-Ekzotermik, Entalpi, Hess Yasası)",
            "Kimyasal Tepkimelerde Hız (Tepkime Hızını Etkileyen Faktörler)",
            "Kimyasal Tepkimelerde Denge (Sulu Çözelti Dengeleri, Asit-Baz Dengesi, KSS)",
        ],
        "12": [
            "Kimya ve Elektrik (Redoks Tepkimeleri, Elektrotlar, Galvanik Piller, Elektroliz)",
            "Karbon Kimyasına Giriş (Hibritleşme, Molekül Geometrisi, Doğadaki Karbon)",
            "Organik Bileşikler (Hidrokarbonlar, Alkoller, Eterler, Karbonil Bileşikleri, Karboksilik Asitler, Esterler)",
            "Enerji Kaynakları ve Bilimsel Gelişmeler",
        ],
    },
    "Biyoloji": {
        "9": [
            "Yaşam Bilimi Biyoloji (Canlıların Ortak Özellikleri, Organik ve İnorganik Bileşikler)",
            "Hücre (Hücre Zarı ve Madde Geçişleri, Organeller, Hücre Teorisi)",
            "Canlıların Çeşitliliği ve Sınıflandırılması (Sınıflandırma İlkeleri, Canlı Alemleri)",
        ],
        "10": [
            "Hücre Bölünmeleri (Mitoz, Eşeysiz Üreme, Mayoz, Eşeyli Üreme)",
            "Kalıtımın Genel İlkeleri (Mendel İlkeleri, Çaprazlamalar, Eşeye Bağlı Kalıtım, Soyağaçları)",
            "Ekosistem Ekolojisi ve Güncel Çevre Sorunları (Besin Zinciri, Madde Döngüleri, Biyoçeşitlilik)",
        ],
        "11": [
            "İnsan Fizyolojisi (Denetleyici ve Düzenleyici Sistemler, Duyu Organları)",
            "Destek ve Hareket Sistemi",
            "Sindirim Sistemi",
            "Dolaşım ve Lenf Sistemleri (Bağışıklık)",
            "Solunum Sistemi",
            "Üriner (Boşaltım) Sistem",
            "Üreme Sistemi ve İnsanda Gelişme",
            "Komünite ve Popülasyon Ekolojisi",
        ],
        "12": [
            "Genden Proteine (Nükleik Asitler, DNA Replikasyonu, Protein Sentezi)",
            "Canlılarda Enerji Dönüşümleri (Hücresel Solunum, Fotosentez, Kemosentez)",
            "Bitki Biyolojisi (Bitkisel Dokular, Organlar, Bitkilerde Madde Taşınması, Büyüme ve Hareket)",
            "Canlılar ve Çevre (Adaptasyon, Doğal Seleksiyon, Genetik Mühendisliği ve Biyoteknoloji)",
        ],
    },
    "Tarih": {
        "9": [
            "Tarih ve Zaman (Tarih Biliminin Yöntemi, Takvimler)",
            "İnsanlığın İlk Dönemleri (İlk Çağ Uygarlıkları, Göçebe ve Yerleşik Yaşam)",
            "Orta Çağ'da Dünya (Siyasi Organizasyon Türleri, Hukuk, İktisat)",
            "İlk ve Orta Çağlarda Türk Dünyası (İlk Türk Devletleri, Kültür ve Medeniyet)",
            "İslam Medeniyetinin Doğuşu (İslamiyet'in Yayılışı, Dört Halife ve Türk-İslam İlişkileri)",
            "Türklerin İslamiyet'i Kabulü ve İlk Türk-İslam Devletleri (Karahanlılar, Gazneliler, Büyük Selçuklular)",
        ],
        "10": [
            "Yerleşme ve Devletleşme Sürecinde Selçuklu Türkiyesi (Anadolu Selçuklu Devleti, Beylikler)",
            "Beylikten Devlete Osmanlı Siyaseti (1302-1453 Kuruluş Dönemi Siyasi Gelişmeleri)",
            "Devletleşme Sürecinde Savaşçılar ve Askerler (Osmanlı Askeri Teşkilatının Kuruluşu)",
            "Beylikten Devlete Osmanlı Medeniyeti (Sosyal Yapı, Tımar Sistemi, İlim ve Sanat)",
            "Dünya Gücü Osmanlı (1453-1595 Yükselme Dönemi, Fetihler ve Diplomasi)",
            "Sultan ve Osmanlı Merkez Teşkilatı (Topkapı Sarayı, Divan-ı Hümayun, Veraset)",
            "Klasik Çağda Osmanlı Toplum Düzeni (Millet Sistemi, Taşra ve Şehir Yaşamı)",
        ],
        "11": [
            "Değişen Dünya Dengeleri Karşısında Osmanlı Siyaseti (1595-1700 Arayış Yılları ve Diplomasi)",
            "Değişim Çağında Avrupa ve Osmanlı (Aydınlanma, Coğrafi Keşifler, Osmanlı Sosyo-Ekonomik İsyanları)",
            "Uluslararası İlişkilerde Denge Stratejisi (1774-1914 Osmanlı Toprak Kayıpları ve Şark Meselesi)",
            "Devrimler Çağında Değişen Devlet-Toplum İlişkileri (Fransız İhtilalı, Anayasal Hareketler, Tanzimat, Islahat, Meşrutiyet)",
            "Sermaye ve Emek (Endüstri Devrimi, Kapitalizm, Osmanlı Sanayileşme Çabaları)",
            "XIX. ve XX. Yüzyılda Toplumsal Hayattaki Değişimler (Nüfus Hareketleri, Modern Kentler, Popüler Kültür)",
        ],
        "12": [
            "XX. Yüzyıl Başlarında Osmanlı Devleti ve Dünya (Trablusgarp, Balkan Savaşları, I. Dünya Savaşı)",
            "Milli Mücadele (Hazırlık Dönemi, Amasya, Erzurum, Sivas, TBMM'nin Açılışı, Antlaşmalar)",
            "Doğu, Güney ve Batı Cepheleri (Düzenli Ordu, Sakarya, Büyük Taarruz, Mudanya, Lozan)",
            "Atatürkçülük ve Türk İnkılabı (Siyasi, Hukuki, Eğitsel, Toplumsal ve Ekonomik İnkılaplar)",
            "İki Dünya Savaşı Arasındaki Dönemde Türkiye ve Dünya (Atatürk Dönemi Dış Politika, Totaliter Rejimler)",
            "II. Dünya Savaşı Sürecinde ve Sonrasında Türkiye ve Dünya (Savaş Yılları, Soğuk Savaş, Türkiye'nin Çok Partili Hayata Geçişi)",
            "Toplumsal Devrim Çağında Dünya ve Türkiye (Yumuşama Dönemi, Küreselleşme, Günümüz Siyasi Gelişmeleri)",
        ],
    },
    "Coğrafya": {
        "9": [
            "Doğal Sistemler (Doğa ve İnsan, Coğrafi Koordinatlar, Harita Bilgisi)",
            "Dünya'nın Şekli ve Hareketleri (Eksen Eğikliği, Mevsimler)",
            "Atmosfer ve İklim (Sıcaklık, Basınç, Rüzgarlar, Nem, Yağış, İklim Tipleri)",
            "Beşeri Sistemler (Yerleşme Türleri ve Yerleşmeyi Etkileyen Faktörler)",
            "Mekânsal Bir Sentez: Türkiye (Türkiye'nin Konumu, İklimi ve Yerleşme Özellikleri)",
            "Çevre ve Toplum (Doğal Afetler ve İnsan Etkisi)",
        ],
        "10": [
            "Doğal Sistemler (Dünya'nın Tektonik Oluşumu, İç ve Dış Kuvvetler)",
            "Su, Toprak ve Bitki Varlığı (Dünyada ve Türkiye'de Su, Toprak, Bitki Örtüsü)",
            "Beşeri Sistemler (Nüfusun Yapısı, Nüfus Piramitleri, Göç Nedenleri ve Sonuçları)",
            "Ekonomik Faaliyetlerin Sınıflandırılması (Birincil, İkincil, Üçüncül vb. Faaliyetler)",
            "Uluslararası Ulaşım Hatları (Kara, Deniz, Hava ve Demiryolları, Boğazlar/Kanallar)",
            "Doğal Afetler (Afet Türleri, Erken Uyarı Sistemleri ve Korunma Yolları)",
        ],
        "11": [
            "Biyoçeşitlilik ve Ekosistemler (Enerji Akışı, Madde Döngüleri)",
            "Nüfus Politikaları ve Şehirlerin Fonksiyonları (Geleceğin Nüfusu, Şehirlerin Etki Alanları)",
            "Türkiye'de Nüfus, Yerleşme ve Ekonomi (Ekonomi Politikaları, Tarım, Hayvancılık, Madencilik, Sanayi)",
            "Küresel Ticaret ve Turizm (Pazar Alanları, Bölgesel Birlikler)",
            "Çevre ve Toplum (Çevre Sorunları, Arazi Kullanımı, Sürdürülebilir Yaşam)",
        ],
        "12": [
            "Küresel Bölgesel Örgütler (Siyasi, Askeri ve Ekonomik Örgütler)",
            "Türkiye'nin Jeopolitik Konumu ve Bölgesel Etkileri (Kıtalararası Geçiş, Enerji Koridorları)",
            "Türkiye'de Bölgesel Kalkınma Projeleri (GAP, DAP, DOKAP, ZBK vb.)",
            "Küreselleşen Dünya ve Çevre Sorunları (Klimatik Değişimler, Doğal Kaynak Yönetimi)",
        ],
    },
    "Felsefe": {
        "9": [],
        "10": [
            "Felsefeyi Tanıma (Düşünme, Sorgulama, Felsefi Düşüncenin Nitelikleri)",
            "Felsefe ile Düşünme (Akıl Yürütme, Argümantasyon, Dil-Düşünce İlişkisi)",
            "Felsefenin Temel Disiplinleri ve Sorunları (Varlık, Bilgi, Bilim, Ahlak, Din, Siyaset, Sanat Felsefesi)",
            "Felsefi Okuma ve Yazma (Metin Analizi ve Deneme Yazma)",
        ],
        "11": [
            "MÖ 6. Yüzyıl - MS 2. Yüzyıl Felsefesi (İlk Çağ Doğa ve İnsan Felsefesi, Sistemleşme)",
            "MS 2. Yüzyıl - MS 15. Yüzyıl Felsefesi (Hristiyan ve İslam Felsefesi)",
            "15. Yüzyıl - 17. Yüzyıl Felsefesi (Rönesans, Akılcılık, Bilimsel Devrim)",
            "17. Yüzyıl - 19. Yüzyıl Felsefesi (Aydınlanma, Aydınlanma Düşünürleri)",
            "19. Yüzyıl - 20. Yüzyıl Felsefesi (Varoluşçuluk, Hermeneutik, Pozitivizm, Çağdaş Akımlar)",
        ],
        "12": [],
    },
    "Din Kültürü ve Ahlak Bilgisi": {
        "9": [
            "Bilgi ve İnanç (Bilgi Kaynakları, İman-Bilgi İlişkisi)",
            "Din ve İslam (Dinin Tanımı, İslam'ın İnanç Esasları)",
            "İslam ve İbadet (İbadetin Anlamı, Özellikleri ve Yükümlülükleri)",
            "Gençlik ve Değerler (Ahlaki Değerler, Kur'an'dan Genç Örnekler)",
            "Gönül Coğrafyamız (İslam Kültür ve Medeniyetinin Yayıldığı Alanlar)",
        ],
        "10": [
            "Allah-İnsan İlişkisi (İnsanın Doğası, Allah'ın İsim ve Sıfatları, Dua)",
            "Hz. Muhammed ve Gençlik (Peygamberimizin Hayatı, Genç Sahabiler)",
            "Din ve Hayat (Hukuk, Aile, İktisat ve Tüketim Ahlakı)",
            "Ahlaki Tutum ve Davranışlar (Kötü Alışkanlıklar, Doğruluk, Adalet)",
            "İslam Düşüncesinde Yorumlar (Mezheplerin Doğuşu, Ameli ve İtikadi Mezhepler)",
        ],
        "11": [
            "Dünya ve Ahiret (Ölüm, Kıyamet, Ahiret Hayatının Aşamaları)",
            "Kur'an'a Göre Hz. Muhammed (Peygamberlik Yönü, Örnek Şahsiyeti)",
            "Kur'an'da Bazı Kavramlar (Hidayet, İhsan, Takva, Cihat vb.)",
            "İnançla İlgili Meseleler (Ateizm, Deizm, Agnostisizm, Nihilizm Sorgulamaları)",
            "İslam ve Bilim (Müslüman Bilim İnsanları, Medeniyet Bahçeleri)",
        ],
        "12": [
            "İslam Düşüncesinde Tasavvufi Yorumlar (Tasavvufun Doğuşu, Tarikatlar ve Ahlak)",
            "Dinî Meselelere Çözümler (Güncel İnanç, İbadet, Sosyal ve Tıbbi Konular)",
            "Hint ve Doğu Asya Dinleri (Hinduizm, Budizm, Konfüçyüsçülük, Taoizm)",
            "Günümüz Dünya Dinleri (Yahudilik, Hristiyanlık, İslamiyet Karşılaştırmaları)",
        ],
    },
}

MAARIF = {
    "Türk Dili ve Edebiyatı": {
        "9": [
            "Sözün İnceliği (Edebiyat, Dil ve İletişim)",
            "Anlatımın Gücü (Metin Türleri ve Metin Yapısı)",
            "Şiirin Dünyası (Ahenk, İmge ve Anlam)",
            "Hikâye Etmenin Büyüsü (Olay Örgüsü, Kişi, Zaman ve Mekân)",
            "Tiyatronun Sahnesi (Diyalog, Çatışma ve Sahneleme)",
            "Düşüncenin İfadesi (Bilgilendirici Metinler, Makale ve Deneme)",
        ],
        "10": [
            "Türk Edebiyatının Tarihsel Yolculuğu (Dönemler ve Köşe Taşları)",
            "Sözlü Kültürden Yazılı Kültüre (Destan, Efsane, Halk Hikayesi)",
            "Divan ve Halk Şiirinin Yapısı (Biçim, Tür ve Anlatım)",
            "Tanzimat'tan Cumhuriyet'e Hikâye ve Roman",
            "Geleneksel Türk Tiyatrosu ve Modern Tiyatro",
            "Gazete Çevresinde Gelişen Metin Türleri",
        ],
        "11": [
            "Toplumcu ve Eleştirel Edebiyat Metinleri",
            "Cumhuriyet Dönemi Şiir Eğilimleri",
            "Cumhuriyet Dönemi Roman ve Hikâye Anlayışları",
            "Düşünce Yazıları ve Eleştiri Metinleri",
            "Cumhuriyet Dönemi Tiyatrosu",
            "Mülakat, Röportaj ve Söylev Metinleri",
        ],
        "12": [
            "Modern ve Postmodern Edebiyat Yönelimleri",
            "1980 Sonrası Türk Şiiri ve Romanı",
            "Dünya Edebiyatından Seçme Metinler",
            "Biyografi, Otobiyografi ve Anı",
            "Deneme ve Felsefi Metin Okumaları",
        ],
    },
    "Matematik": {
        "9": [
            "Sayılar ve Nicelikler (Küme ve Mantık Sembolizmi Azaltılmış Sayısal İlişkiler)",
            "Değişimler ve İlişkiler (Fonksiyonel Düşünme, Denklemler ve Eşitsizlikler)",
            "Geometrik Şekiller ve Ölçme (Üçgenlerde İlişkiler, Vektörel ve Görsel Modelleme)",
            "Veriden Olasılığa (İstatistiksel Araştırma Süreci ve Olasılık)",
        ],
        "10": [
            "Veri Analizi ve Veri Modelleme",
            "Kombinatorik Sayma ve Olasılık",
            "Fonksiyonel İlişkiler ve Değişim Modelleri",
            "Polinom İfadeleri ve Denklem Çözümleri",
            "Düzlem Geometrisi ve Çokgenler",
        ],
        "11": [
            "Dairesel Fonksiyonlar ve Trigonometrik İlişkiler",
            "Analitik Düzlemde Doğru ve Değişim",
            "Cebirsel ve Grafiksel Fonksiyon Modelleri (Parabol)",
            "Çember, Daire ve Uzamsal Cisimler",
            "Deneysel ve Teorik Olasılık",
        ],
        "12": [
            "Üstel ve Logaritmik Modeller",
            "Dizi ve Dizi Aritmetiği",
            "İleri Trigonometrik Eşitlikler",
            "Dönüşümler ve Analitik Geometri",
            "Limit ve Anlık Değişim",
        ],
    },
    "Geometri": {
        "9": [
            "Üçgenlerin Geometrisi ve Doğrusal İlişkiler",
            "Trigonometrik Oranlar ve Modeller",
        ],
        "10": [
            "Düzlemde Çokgenler ve Dörtgenler",
            "Uzayda Geometri ve Katı Cisim Özellikleri",
        ],
        "11": [
            "Analitik Geometri (Nokta ve Doğru)",
            "Çember ve Daire Geometrisi",
            "Yüzey Alanı ve Hacim Hesaplamaları",
        ],
        "12": [
            "Dönüşüm Geometrisi (Öteleme, Dönme, Simetri)",
            "Çemberin Analitik İncelemesi",
        ],
    },
    "Fizik": {
        "9": [
            "Fiziksel Büyüklükler ve Model Oluşturma",
            "Hareket, Kuvvet ve Newton Yasaları",
            "İş, Güç, Enerji ve Verim",
            "Termodinamik ve Isıl Denge",
        ],
        "10": [
            "Elektrik Devreleri ve Manyetizma",
            "Basınç, Akışkanlar ve Kaldırma Kuvveti",
            "Dalga Hareketi ve Dalga Türleri",
            "Işık, Yansıma, Kırılma ve Optik Aletler",
        ],
        "11": [
            "Vektörel İnceleme ve Bağıl Hareket",
            "Sabit İvmeli Hareket ve Atışlar",
            "Kuvvet, Tork, Denge ve Momentum",
            "Elektriksel ve Manyetik Alanlar",
            "Alternatif Akım ve İndüksiyon",
        ],
        "12": [
            "Düzgün Çembersel Hareket ve Açısal Momentum",
            "Basit Harmonik Hareket ve Titreşim",
            "Dalga Mekaniği ve Işık Teorileri",
            "Modern Fizik ve Atom Kuramları",
            "Teknolojide Modern Fizik Uygulamaları",
        ],
    },
    "Kimya": {
        "9": [
            "Kimya Bilimi, Güvenlik ve Sürdürülebilirlik",
            "Atom Yapısı, Kuantum Modelleri ve Periyodik Eğilimler",
            "Kimyasal Türler Arası Etkileşimler",
            "Maddenin Fiziksel Halleri ve Moleküler Yapı",
        ],
        "10": [
            "Kimyasal Tepkimeler ve Nicel İlişkiler (Mol)",
            "Karışımlar ve Çözelti Dinamikleri",
            "Asitler, Bazlar, Tuzlar ve Tepkimeleri",
            "Çevre Kimyası ve Yeşil Kimya",
        ],
        "11": [
            "Atomun Elektronik Yapısı",
            "Gaz Yasaları ve İdeal Gaz Modelleri",
            "Çözeltiler ve Koligatif Özellikler",
            "Tepkimelerde Enerji Değişimi (Entalpi)",
            "Tepkime Hızı ve Kimyasal Denge",
        ],
        "12": [
            "Elektrokimyasal Hücreler ve Redoks",
            "Karbon Kimyası ve Moleküler Geometri",
            "Organik Bileşikler ve Fonksiyonel Gruplar",
            "Enerji Kaynakları ve Sürdürülebilir Malzemeler",
        ],
    },
    "Biyoloji": {
        "9": [
            "Yaşamın Biyokimyasal Temelleri",
            "Hücresel Yapı, Organel Ağları ve Madde Geçişleri",
            "Canlıların Çeşitliliği ve Sınıflandırma Mantığı",
        ],
        "10": [
            "Hücre Döngüsü, Mitoz ve Mayoz",
            "Kalıtım, Genetik Biyoçeşitlilik ve Soyağaçları",
            "Ekosistem Dinamikleri ve Sürdürülebilir Çevre",
        ],
        "11": [
            "İnsan Fizyolojisi ve Denetleyici Sistemler",
            "Destek, Hareket ve Dolaşım Sistemleri",
            "Solunum, Boşaltım ve Üreme Sistemleri",
            "Komünite ve Popülasyon Ekolojisi",
        ],
        "12": [
            "Nükleik Asitler, Genetik Kod ve Protein Sentezi",
            "Hücresel Enerji Dönüşümleri (Fotosentez, Kemosentez, Solunum)",
            "Bitki Biyolojisi ve Taşıma Mekanizmaları",
            "Genetik Mühendisliği, Biyoteknoloji ve Etik",
        ],
    },
    "Tarih": {
        "9": [
            "Tarihsel Bilgi ve Zaman Kavrayışı",
            "Eski Çağ'da İnsan ve Mekân",
            "Orta Çağ'da Siyasi ve Sosyal Yapılar",
            "İlk ve Orta Çağlarda Türk Dünyası",
            "İslam Medeniyetinin Doğuşu ve Yayılışı",
        ],
        "10": [
            "Anadolu'da Selçuklu ve Beylikler Dönemi",
            "Beylikten Devlete Osmanlı Kurumları",
            "Klasik Dönem Osmanlı Medeniyeti ve Mülki Yapı",
            "Küresel Güç Osmanlı (15.-16. Yüzyıl)",
            "Osmanlı Toplum Yapısı ve Askerî Düzen",
        ],
        "11": [
            "Değişen Dünya Dengeleri ve Osmanlı Diplomasi Düzeneği",
            "Avrupa'daki Gelişmeler ve Osmanlı Sosyo-Ekonomik Değişimi",
            "Uluslararası İlişkilerde Denge Siyaseti",
            "Modernleşme Sürecinde Osmanlı ve Anayasal Hareketler",
        ],
        "12": [
            "XX. Yüzyıl Başlarında Dünya ve Osmanlı",
            "Milli Mücadele ve Bağımsızlık Savaşı",
            "Atatürkçülük, İnkılaplar ve Türkiye Cumhuriyeti'nin Kuruluşu",
            "İki Dünya Savaşı Arasındaki Türkiye ve Dünya",
            "Soğuk Savaş, Küreselleşme ve Çağdaş Türkiye Tarihi",
        ],
    },
    "Coğrafya": {
        "9": [
            "Coğrafi Düşünce ve Harita Okuryazarlığı",
            "Doğal Sistemler: Dünya, İklim ve Hava Olayları",
            "Beşerî Sistemler: Yerleşme Doku ve Tipleri",
            "Sürdürülebilir Çevre ve Doğal Afet Yönetimi",
        ],
        "10": [
            "Yeryüzünün Şekillenmesi ve İç/Dış Kuvvetler",
            "Doğal Kaynaklar: Su, Toprak ve Bitki Örtüsü",
            "Nüfus Dinamikleri, Yapısı ve Göçler",
            "Ekonomik Faaliyet Türleri ve Ulaşım Ağları",
        ],
        "11": [
            "Biyoçeşitlilik, Madde Döngüleri ve Ekosistem Hizmetleri",
            "Nüfus Politikaları ve Şehirlerin Küresel Etkisi",
            "Türkiye Ekonomi Coğrafyası (Tarım, Sanayi, Hizmet)",
            "Bölgesel ve Küresel Ticaret Ağları",
        ],
        "12": [
            "Jeopolitik Konum ve Türkiye'nin Bölgesel Rolü",
            "Türkiye'de Bölgesel Kalkınma Stratejileri",
            "Küresel Örgütler ve İttifaklar",
            "Çevresel Sorunlar, İklim Değişikliği ve Gelecek Projeksiyonları",
        ],
    },
    "Felsefe": {
        "9": [],
        "10": [
            "Felsefi Soru Sorma ve Akıl Yürütme Becerileri",
            "Varlık, Bilgi ve Değer Felsefesi",
            "Ahlak, Sanat, Siyaset ve Din Felsefesi Problem Alanları",
            "Felsefi Metin İnceleme ve Argümantasyon Oluşturma",
        ],
        "11": [
            "Antik Çağ ve Orta Çağ Düşünce Gelenekleri",
            "Rönesans ve Modern Felsefenin Doğuşu",
            "18-19. Yüzyıl Aydınlanma Felsefesi",
            "20. Yüzyıl ve Çağdaş Felsefe Akımları",
        ],
        "12": [],
    },
    "Din Kültürü ve Ahlak Bilgisi": {
        "9": [
            "İnanç, Bilgi ve İnsan",
            "İslam ve İbadet Hayatı",
            "Gençlik, Değerler ve Ahlak",
            "Kültür, Medeniyet ve Gönül Coğrafyamız",
        ],
        "10": [
            "Allah-İnsan İletişimi ve Dua",
            "Hz. Muhammed'in Gençlik Yılları ve Örnekliği",
            "Din, Aile ve Sosyal Hayat",
            "İslam Düşüncesindeki İtikadi ve Ameli Yorumlar",
        ],
        "11": [
            "Ahiret İnancı ve Hayatın Anlamı",
            "Hz. Muhammed'in Peygamberlik Yönü",
            "Kur'an-ı Kerim'in Temel Kavramları",
            "Çağdaş İnanç Meseleleri ve Felsefi Yaklaşımlar",
        ],
        "12": [
            "Tasavvufi Yorumlar ve Ahlak Terbiyesi",
            "Güncel Dini ve Etik Sorunlara Yaklaşımlar",
            "Yaşayan Dünya Dinleri ve İnanç Biçimleri",
        ],
    },
}


def seed(apps, schema_editor):
    Subject = apps.get_model('Rehberim', 'Subject')
    Topic = apps.get_model('Rehberim', 'Topic')
    # Bu migration konu kataloğunun tek doğru kaynağıdır; önceki ad-hoc seed'i
    # (0008) temizleyip PDF'lerden yeniden kuruyoruz.
    Topic.objects.all().delete()

    for curriculum, data in (('eski', ESKI), ('maarif', MAARIF)):
        for subject_name, grades in data.items():
            subject = Subject.objects.filter(name=subject_name, category='okul').first()
            if subject is None:
                continue
            for grade, topics in grades.items():
                for order, name in enumerate(topics):
                    Topic.objects.get_or_create(
                        subject=subject, grade=grade, curriculum=curriculum,
                        name=name, defaults={'order': order},
                    )


def unseed(apps, schema_editor):
    Topic = apps.get_model('Rehberim', 'Topic')
    Topic.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Rehberim', '0009_publisher_alter_topic_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
