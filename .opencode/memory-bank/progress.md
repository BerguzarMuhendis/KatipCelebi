# Progress

## Tamamlanan özellikler (kodda mevcut)
- [x] Book dataclass + ISBN-10/ISBN-13 doğrulama, parse_rating/parse_copies, publish_year
- [x] `Library` (store.py): load/save/add/remove/replace, yinelenen key kurtarma, rollback deseni
- [x] Güvenli depolama: atomik yazma, bozuk dosya kurtarma, backup (storage.py)
- [x] `Ledger` (people/store.py): kişi ekleme/silme, ödünç verme/geri alma, trust_score
- [x] Person/Loan modelleri + loan soru fonksiyonları (model.py)
- [x] Open Library entegrasyonu: ISBN sorgusu, kapak indirme + önbellek, kitap katkılama (openlibrary.py)
- [x] Arka plan kapak yükleme (thread pool) + placeholder çizimi (covers.py)
- [x] Etiket sistemi + Open Library subjects temizliği (tags.py)
- [x] Excel dışa aktarım (formül enjeksiyon korumalı) + ISBN şablonu içe aktarım (excel.py)
- [x] 6 tema (M3 açık/koyu, Adwaita açık/koyu, system, custom) (theme.py)
- [x] Material Design 3 renk motoru (palette.py)
- [x] Çok dilli metinler: en, tr, ru, zh, es, fr (texts.py + assets/lang)
- [x] Ayarlar (settings.json, config.py), klasör taşıma (relocate.py)
- [x] İstatistikler (QtCharts), özet (summary.py), hedefler (goals.py)
- [x] Ana pencere, sidebar, setup/welcome akışı, kitap detay sayfası (app.py)
- [x] PyInstaller spec (KatipCelebi.spec)

## Doğrulanmamış / yapılmadı
- [ ] Uygulama hiç çalıştırılmadı (bağımlılıklar kurulmadı)
- [ ] Test dosyası yok
- [ ] Repo bir git deposuna dönüştürülmedi

## Bilinen kısıtlamalar
- Open Library bir wiki olduğundan şema tutarsız; her alan ayrı ayrı dirençli okunur
- Kapak önbelleği diskte `<isbn>_<size>.jpg`; `fetch_cover` önce önbelleğe bakar
- Windows'ta `_fsync_dir` sessizce atlanır

## Roadmap (projeden çıkarılan)
- Linux için .deb / .rpm / .pkg.tar.zst paketleme komutları README'de hazır (fpm ile)
- Custom tema: kullanıcı `custom.qss` dosyasıyla kendi görünümünü yapar
- Yeni dil eklemek: `assets/lang/xx.json` + `FLAG_FOR_LANGUAGE` girişi
