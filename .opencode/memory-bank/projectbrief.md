# Project Brief

## Ne yapar
Katip Celebi, PyQt6 ile yazılmış bir masaüstü kütüphane (kitap arşivi) yöneticisidir. Kitapları yönetmek, ödünç verme geçmişini tutmak, okuma hedefleri ve istatistikleri izlemek için tasarlanmıştır.

## Kapsam (temel özellikler)
- **Kitap ekleme/düzenleme/silme** — Open Library ISBN sorgusu ile otomatik doldurma
- **ISBN liste içe aktarımı** — `.xlsx` şablonuna yapıştırılan ISBN'leri toplu ekleme (max 20 MiB)
- **Ödünç takibi** — kim, hangi kitabı, ne zaman aldı; çoklu kopya desteği
- **Okuma istatistikleri** — grafikler, yıllık/aylık okuma hedefleri
- **Temalar** — Material 3 (açık/koyu), Adwaita (açık/koyu), sistem tercihi, custom QSS
- **Çok dilli arayüz** — İngilizce, Türkçe, Rusça, Çince, İspanyolca, Fransızca
- **Excel dışa aktarım** — formül enjeksiyonuna karşı korumalı
- **Çapraz platform** — Windows ve Linux

## Hedef kullanıcı
Kişisel kütüphanesini ve arkadaşlarına/öğrencilere verdiği kitapları takip etmek isteyen bireysel kullanıcı.

## Lisans
- **Kaynak kod:** GPLv3
- **Görsel varlıklar:** Apache 2.0

## Not
Proje tamamen "Vibe Coding" ile geliştirilmiştir (README'de belirtilmiş).
