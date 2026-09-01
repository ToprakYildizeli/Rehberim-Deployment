# Referans belgeler

Ürünün içerik kaynakları. **Bunlar referanstır, veri kaynağı değildir** —
uygulamalar bu listeleri koda gömmez, backend'den çeker.

| Dosya | İçerik | Backend'deki karşılığı |
|---|---|---|
| `Konular.pdf` | TYT/AYT sınav konu listesi (eski müfredat) | `Topic` · `GET /api/topics/?subject=` |
| `Maarif Konular.pdf` | Okul dersleri konu listesi (Maarif müfredatı, 9–12. sınıf) | `Topic` (`curriculum=maarif`) |
| `Yayinevleri.pdf` | Yayınevi listesi | `Publisher` · `GET /api/publishers/` |

## Nasıl kullanılır

Üçünün içeriği de backend'de **data migration** olarak seed'lenmiş durumda; API
üzerinden hazır gelir:

```
GET /api/subjects/                    → dersler (TYT / AYT / okul)
GET /api/topics/?subject=<id>         → seçilen dersin konuları
GET /api/topics/?subject=<id>&grade=11&curriculum=maarif
GET /api/publishers/                  → yayınevleri
```

Yeni bir ekranda ders, konu ya da yayınevi seçimi gerekiyorsa **serbest metin
kutusu değil**, bu uçlardan beslenen bir seçim listesi kullanın. Aynı veri iki
yerde farklı yazılırsa eşleşme bozulur.

PDF'ler burada, listenin doğruluğunu gözle kontrol etmek ya da eksik bir konu
fark edildiğinde backend'e bildirmek için duruyor. Bir şey eksikse backend
tarafında seed migration'ı güncellenir — PDF'i düzenlemek bir şeyi değiştirmez.
