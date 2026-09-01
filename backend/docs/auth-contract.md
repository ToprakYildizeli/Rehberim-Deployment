# Rehberim — Auth API Kontratı

> **Sürüm:** v2.0 · **Durum:** DONDURULDU (frontend onayladı, 2026-07-09) · **Tarih:** 2026-08-29
>
> Bu dosya frontend (React-rehber, Flutter-öğrenci/veli) ile backend arasındaki
> kimlik doğrulama sözleşmesidir. Donduruldu; bir alan/akış değişecekse önce iki
> tarafa haber verilir ve sürüm yükseltilir. `TASLAK` işaretli birkaç kısım hâlâ
> genişleyebilir — o alanlara sıkı bağlanmayın.
>
> **v1.1 (2026-08-21):** `PATCH /api/auth/me/` eklendi (§5.4b). Geriye dönük
> uyumlu — mevcut hiçbir uç/alan değişmedi, yalnızca yeni bir metot geldi.
>
> **v2.0 (2026-08-29) — KIRICI DEĞİŞİKLİK, yalnız veli akışında (E3):**
> Veli artık öğrencinin `connect_code`'u ile değil, **öğrencinin id'si + o
> öğrencinin rehberinin davet kodu** ile bağlanıyor. Etkilenen iki yer:
> `POST /api/auth/register/parent/` (§5.7) ve `POST /api/parents/connect-student/`
> (§5.9) — `student_code` / `code` alanları kalktı, yerlerine `student` +
> `counselor_code` geldi. Öğrenci ve rehber akışlarında **hiçbir değişiklik yok**.
> Veli mobil uygulaması henüz yazılmadığı için sahada kırılan istemci yok.

## 1. Temel bilgiler

- **Base URL (dev):** `http://127.0.0.1:8000/api/`
- **Format:** JSON (`Content-Type: application/json`)
- **Auth mekanizması:** JWT (access + refresh).
- **Korumalı isteklerde header:** `Authorization: Bearer <access_token>`

## 2. Token akışı

- `login` / `register` → `access` (kısa ömürlü) + `refresh` (uzun ömürlü) döner.
- Her korumalı istekte `access` header'a konur.
- `access` süresi dolunca istek **401** döner → `POST /api/auth/refresh/` ile yeni
  `access` al, isteği bir kez tekrarla. Refresh de geçersizse kullanıcıyı login'e at.
- Çıkışta `refresh` token blacklist'e alınır (`logout`).

### Token ömürleri (TASLAK)
- access: ~30 dk · refresh: ~7 gün. (Kesinleşince güncellenecek.)

## 3. Rol

Kullanıcı objesindeki `role` alanı: `"counselor" | "student" | "parent"`.
Frontend menü ve yönlendirmeyi buna göre kurar.

## 4. Kullanıcı objesi (`user`)

`login`, `register` ve `me` yanıtlarında dönen ortak yapı:

```json
{
  "id": 1,
  "username": "ayse",
  "email": "ayse@example.com",
  "first_name": "Ayşe",
  "last_name": "Yılmaz",
  "role": "student",
  "profile": { }   // role'e göre değişir — TASLAK, aşağıya bak
}
```

**`profile` içeriği (TASLAK):**
- `counselor` → `{ "invite_code": "AB12CD" }`
- `student` → `{ "grade": "12", "study_field": "say", "counselor": null }`
- `parent` → `{ "students": [ { "id": 3, "name": "Ali Yılmaz" } ] }`

## 5. Endpoint'ler

### 5.1 Giriş
```
POST /api/auth/login/
→ { "username": "ayse", "password": "..." }
← 200 { "access": "...", "refresh": "...", "user": { ...bkz. §4 } }
← 401 { "detail": "Kullanıcı adı veya şifre hatalı." }
```

### 5.2 Token yenileme
```
POST /api/auth/refresh/
→ { "refresh": "..." }
← 200 { "access": "..." }
← 401 { "detail": "Token geçersiz veya süresi dolmuş." }
```

### 5.3 Çıkış
```
POST /api/auth/logout/      (Bearer gerekli)
→ { "refresh": "..." }
← 205  (içerik yok)
```

### 5.4 Ben kimim
```
GET /api/auth/me/           (Bearer gerekli)
← 200 { ...bkz. §4 kullanıcı objesi }
```

### 5.4b Profilimi güncelle  *(v1.1 — 2026-08-21'de eklendi)*
```
PATCH /api/auth/me/         (Bearer gerekli)
→ { "first_name": "Ayşegül", "last_name": "Kaya", "email": "yeni@x.com" }
← 200 { ...bkz. §4 kullanıcı objesi }   // GET ile birebir aynı şekil
```
Üç alan da **opsiyoneldir** (kısmi güncelleme); gönderilmeyen alan değişmez.

- `username` ve rol bayrakları **düzenlenemez** — gövdede gönderilirlerse sessizce yok sayılır.
- Boş string kabul edilmez (`""` → `400`).
- E-posta benzersizliği kayıttaki kuralla aynıdır, ama kullanıcının **kendi** mevcut
  e-postasını yeniden göndermesi çakışma sayılmaz.

| Durum | Ne zaman |
|---|---|
| `400` | Boş ad/soyad, geçersiz e-posta, başkasının kullandığı e-posta |
| `401` | Token yok/geçersiz |

### 5.5 Kayıt — Rehber (web/React)
```
POST /api/auth/register/counselor/
→ { "username", "email", "password", "first_name", "last_name" }
← 201 { "access", "refresh", "user": { ...role: "counselor" } }
```

### 5.6 Kayıt — Öğrenci (mobil/Flutter)
```
POST /api/auth/register/student/
→ {
    "username", "email", "password", "first_name", "last_name",
    "grade": "12",              // 9 | 10 | 11 | 12 | mezun
    "study_field": "say",       // say | ea | soz  (9-10. sınıfta boş/null)
    "counselor_code": "AB12CD"  // opsiyonel — sonradan da bağlanabilir (§5.8)
  }
← 201 { "access", "refresh", "user": { ...role: "student" } }
```

### 5.7 Kayıt — Veli (mobil/Flutter)
```
POST /api/auth/register/parent/
→ {
    "username", "email", "password", "first_name", "last_name",
    "student": 3,               // opsiyonel — sonradan da bağlanabilir (§5.9)
    "counselor_code": "AB12CD"  // `student` ile BİRLİKTE gönderilir
  }
← 201 { "access", "refresh", "user": { ...role: "parent" } }
← 400 { "counselor_code": ["Öğrenci numarası ile rehber davet kodu eşleşmiyor."] }
← 400 { "counselor_code": ["Öğrenci numarası ve rehber davet kodu birlikte gönderilmelidir."] }
```
İkisi de boş bırakılabilir (bağlanmadan kaydol); ama biri gönderilip diğeri
gönderilmezse `400` döner.

### 5.8 Öğrenci → Rehber bağlama
```
POST /api/students/connect-counselor/   (Bearer, öğrenci)
→ { "code": "AB12CD" }
← 200 { "counselor": { "id": 2, "name": "Mehmet Hoca" } }
← 400 { "code": ["Geçersiz rehber kodu."] }
```

### 5.9 Veli → Öğrenci bağlama  *(v2.0'da değişti)*
```
POST /api/parents/connect-student/       (Bearer, veli)
→ { "student": 3, "counselor_code": "AB12CD" }
← 200 {
    "student":   { "id": 3, "name": "Ali Yılmaz" },
    "counselor": { "id": 2, "name": "Mehmet Hoca" }
  }
← 400 { "counselor_code": ["Öğrenci numarası ile rehber davet kodu eşleşmiyor."] }
```

**Kimlik ikilisi:** `student` = öğrencinin id'si (öğrenci kendi profilinde görür),
`counselor_code` = o öğrencinin **rehberinin** davet kodu. İkisi birlikte
doğrulanır; rehbere bağlı olmayan bir öğrenciye veli bağlanamaz.

**Hata mesajı bilerek tek ve ayrımsız:** "öğrenci yok" ile "kod yanlış" ayrı ayrı
söylenmez, yoksa kodu eline geçiren biri id deneyerek rehberin öğrenci listesini
çıkarabilir. Frontend bu tek mesajı olduğu gibi gösterebilir.

> **Bilinen sınır (kullanıcı kararı, 29 Ağu 2026):** davet kodu bir rehberin
> **tüm** öğrencileri için aynı olduğundan, kodu bilen bir veli id deneyerek aynı
> rehberin başka bir öğrencisine de bağlanabilir. Bilinçli olarak kabul edildi;
> sertleştirmek gerekirse öğrenci soyadı üçüncü alan olarak eklenir.

`Student.connect_code` alanı hâlâ modelde duruyor ama **artık hiçbir akışta
kullanılmıyor**; yeni bir kullanım eklenmeden önce kaldırılması düşünülebilir.

## 6. Hata formatı

| Kod | Anlamı | Frontend davranışı |
|-----|--------|--------------------|
| `400` | Doğrulama hatası: `{"alan": ["mesaj"]}` | Alan altında mesajı göster |
| `401` | Token yok/geçersiz/süresi dolmuş | Refresh dene → olmazsa login'e at |
| `403` | Yanlış rol / yetki yok | "Erişim yok" göster |

## 7. Hangi frontend neyi kullanır

| Endpoint | React (rehber) | Flutter (öğrenci/veli) |
|----------|:---:|:---:|
| login / refresh / logout / me | ✅ | ✅ |
| register/counselor | ✅ | — |
| register/student, register/parent | — | ✅ |
| connect-counselor, connect-student | — | ✅ |

## 8. Token saklama (güvenlik)

- **Flutter:** `flutter_secure_storage` kullanın (düz `SharedPreferences` değil).
- **React:** access'i bellekte tutmak ideali; refresh için httpOnly cookie hedef.
  Pratikte başlangıçta localStorage kabul, sonra sertleştirilecek.

## 9. CORS

Backend yalnızca izin verilen origin'lerden isteği kabul eder. Dev adreslerinizi
backend'e bildirin (örn. React `http://localhost:5173`, Flutter emülatör).
İzin listesine eklenecek.

---

### Açık kalan / karar bekleyen (TASLAK)
- `profile` objesinin tam içeriği (özellikle rehber dashboard'u netleşince).
- Token ömürleri.
- Kayıtta e-posta doğrulaması olacak mı (MVP'de muhtemelen hayır).
