# Rehberim — Başarımlar API Kontratı

> **Sürüm:** v1 · **Durum:** TASLAK · **Tarih:** 2026-08-26
>
> Öğrencinin ulaştığı eşikler: deneme neti, konu tamamlama ve program uyumu.
> Auth: tüm uçlar `Authorization: Bearer <access>` ister.

## 1. Temel kavram

**Başarım tanımı rehbere aittir.** Global bir katalog yoktur; her rehberin kendi
satırları vardır. Yeni bir rehber kaydolduğunda **varsayılan set kendisine
kopyalanır**; sonrasında Ayarlar'dan istediğini siler, ekler ya da eşiğini
değiştirir — bu değişiklik başka hiçbir rehberi etkilemez.

**Kazanım saklanmaz, anlık hesaplanır.** Ayrı bir "kazanılmış başarımlar" tablosu
yoktur: eşik değişince ya da bir deneme silinince kayıtla gerçek arasında
tutarsızlık kalmasın diye durum her istekte yeniden çıkarılır.

## 2. Ölçütler (`metric`)

| `metric` | Ne ölçer | `scope` | Eşik birimi |
|---|---|---|---|
| `exam_net` | O türdeki denemelerin **en yüksek** toplam neti | **zorunlu**: `tyt` / `ayt` | net |
| `topic_completion` | Seviye 5 konuların, öğrencinin kapsamındaki toplam konuya oranı | boş | yüzde (≤100) |
| `compliance` | Onaylı haftaların dakika ağırlıklı uyum yüzdesi (bkz. `program-contract.md` §11) | boş | yüzde (≤100) |

**Neden en yüksek net?** Başarım "bir kez ulaştı" demektir; sonraki kötü bir
deneme kazanılmış başarımı geri almamalı.

**Konu tamamlamada payda** öğrencinin dersleri (`available_subjects()`) ve
müfredatıyla sınırlıdır; ilerleme kaydı olmayan konu tamamlanmamış sayılır.

**Uyum yalnız onaylı haftalardan** gelir — onaysız haftanın beyanı doğrulanmamıştır
(bkz. `program-contract.md` §10).

## 3. Varsayılan set

Yeni rehbere kopyalanan 12 başarım:

- **Deneme neti (TYT):** 60 · 80 · 90 · 100 · 110 net
- **Konu tamamlama:** %25 · %50 · %75 · %100
- **Program uyumu:** %60 · %80 · %100

Bunlar yalnızca **başlangıç** listesidir; rehber hepsini değiştirebilir.

## 4. Tanım uçları (yalnız rehber, yalnız kendi başarımları)

```
GET    /api/achievements/           → rehberin tanımları
POST   /api/achievements/           → { "name", "metric", "scope"?, "threshold",
                                        "description"?, "is_active"?, "order"? }
GET    /api/achievements/{id}/
PATCH  /api/achievements/{id}/
DELETE /api/achievements/{id}/
```

```json
{
  "id": 12,
  "name": "TYT 80 Net",
  "description": "TYT denemesinde 80 net",
  "metric": "exam_net",
  "metric_display": "Deneme Neti",
  "scope": "tyt",
  "threshold": 80.0,
  "is_active": true,
  "order": 1
}
```

`counselor` gövdede **gönderilmez**, sunucuda atanır. Başka rehberin başarımına
erişim `404` döner (varlığını sızdırmamak için `403` değil).

`is_active: false` başarımı **silmeden gizler** — öğrenci durumu listesine girmez.

## 5. Öğrenci durumu

```
GET /api/achievements/progress/?student=<id>
```

- **Öğrenci:** parametresiz kendi durumu (`student` verilse de yok sayılır).
- **Rehber:** `student` zorunlu, yalnız kendi öğrencisi (eksikse `400`, başkasınınsa `404`).
- **Veli:** çocuğu (salt-okur).

```json
{
  "student": 241,
  "student_name": "Ali Yılmaz",
  "earned_count": 4,
  "total_count": 12,
  "facts": {
    "exam_net_tyt": 91.75, "exam_net_ayt": 49.0,
    "topic_completion": 2.1, "topics_done": 6, "topics_total": 286,
    "compliance": 75.7
  },
  "achievements": [
    { "id": 12, "name": "TYT 80 Net", "description": "...", "metric": "exam_net",
      "scope": "tyt", "threshold": 80.0, "value": 91.75,
      "earned": true, "progress": 100 }
  ]
}
```

**Notlar:**

1. Sıralama: **kazanılanlar önce**, sonra eşiğe en yakın olanlar — "sıradaki
   hedef" listenin başında görünsün.
2. `progress` = eşiğin yüzde kaçına gelindiği (0–100); kazanıldıysa her zaman 100.
3. `value` **null** olabilir (ör. hiç deneme girilmemiş) — o başarım kazanılmamış
   sayılır, `progress` 0 olur.
4. `facts` bir kez hesaplanıp bütün başarımlara paylaştırılır; arayüz "6/286 konu"
   gibi bağlam göstermek için doğrudan kullanabilir.
5. **Rehberi olmayan öğrencide liste boştur** (`total_count: 0`) — başarımları
   koyan rehberdir.

## 6. Hatalar

| Kod | Durum |
|-----|-------|
| `400` | `exam_net`'te `scope` yok; yüzde ölçütünde `scope` verildi ya da eşik > 100; eşik ≤ 0; aynı adda başarım var; rehber `student` vermedi |
| `401` | Token yok/geçersiz |
| `403` | Öğrenci/veli tanım uçlarına erişmeye çalıştı |
| `404` | Başka rehberin başarımı; başka rehberin öğrencisi |
