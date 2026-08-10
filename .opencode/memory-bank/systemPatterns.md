# System Patterns

## Mimari genel bakış

```
src/
├── app.py          # Giriş noktası, MainWindow, Setup/Welcome sayfaları
├── books/          # Kitaplık işi
│   ├── model.py    # Book dataclass + ISBN doğrulama + yardımcılar (Qt'siz, dosyasız)
│   ├── store.py    # Library: kitaplar + library.json okuma/yazma
│   ├── tags.py     # Etiketler + Open Library subjects temizliği
│   ├── openlibrary.py # ISBN sorgusu, kapak indirme, kitap katkılama
│   ├── covers.py   # Arka plan kapak yükleme (thread pool) + yer tutucu çizimi
│   ├── add.py      # Kitap ekleme sayfası
│   ├── grid.py     # Kütüphane ızgarası + filtreler
│   ├── card.py     # Kitap kartı widget'ı
│   ├── detail.py   # Kitap detay sayfası
│   ├── lending_panel.py # Ödünç verme paneli
│   ├── excel.py    # Excel dışa aktarım + ISBN şablon içe aktarım
│   ├── personal.py # Kişisel notlar, imza, durum
│   ├── reading.py  # Okuma durumu / tarih ayrıştırma
│   ├── facts.py    # Ödünç/okuma istatistik hesapları
│   └── filters.py  # Arama/filtre yardımcıları
├── people/
│   ├── model.py    # Person + Loan dataclass + soru fonksiyonları
│   ├── store.py    # Ledger: kişiler + loans.json/people.json
│   └── page.py     # Kişiler sayfası
├── stats/
│   ├── page.py     # İstatistik sayfası (QtCharts)
│   ├── summary.py  # Özet istatistikler
│   └── goals.py    # Yıllık/aylık hedefler (goals.json)
├── settings/
│   ├── page.py     # Ayarlar sayfası
│   └── relocate.py # Kütüphane taşıma
└── shared/
    ├── theme.py    # 6 tema, stylesheet üretimi, renk adları (~1186 satır)
    ├── palette.py  # Material Design 3 renk motoru
    ├── icons.py    # SVG ikon boyama, bayraklar, app ikonu
    ├── config.py   # settings.json (AppData) erişimi
    ├── paths.py    # Tüm yollar
    ├── storage.py  # Atomik yazma, bozuk dosya kurtarma
    ├── texts.py    # Çok dilli metinler
    ├── credentials.py # OS kimlik deposu (keyring) — Open Library girişi
    ├── logs.py     # Log yönlendirme
    └── shape.py    # QSS'te kullanılan şekil/kenar tanımları
```

## Temel desenler

### 1. Veri katmanı = dataclass + saf fonksiyonlar
`Book`, `Person`, `Loan` hepsi `@dataclass`; dosya girişi `from_dict`, çıkış `to_dict`. Tüm alanlar string. Model modülleri Qt, dosya ve ağ bilmez (test edilebilirlik).

### 2. "Önce dosyaya yaz, sonra belleğe koy" — rollback deseni
```python
self.books.append(book)
if self.save():
    return True
self.books.pop()          # yazma başarısızsa geri al
return False
```
`Library.add/remove/replace`, `Ledger.add_person/lend/take_back`, `Goals.set_yearly` hepsi bu deseni kullanır.

### 3. Güvenli depolama katmanı (shared/storage.py)
- `write_atomically`: temp dosya → `os.fsync` → `os.replace` → dizin fsync
- `rescue_file`: okunamayan dosyayı `.damaged.bak`, `.damaged.1.bak`... adına taşır
- `read_rows`: yoksa boş liste, bozuksa `DataFileDamaged` fırlatır
- `backup_file`: yeniden yazmadan önce `.bak` kopyası

### 4. Veri dosyaları
- Kullanıcının seçtiği klasörde: `library.json`, `people.json`, `loans.json`, `goals.json` (hepsi JSON nesne listesi)
- AppData'da: `settings.json` (klasör, tema, dil, setup_done), `covers/` (kapak önbelleği), `katipcelebi.log`
- `paths.py` tanımlı; yeni dosya eklerken oradan tanımla

### 5. Konfigürasyon tek noktadan
`config.py` — `library_dir()`, `theme()`, `language()`, `setup_done()` + setter'lar. Bozuk/elle düzenlenmiş settings.json'a dayanıklı (`isinstance` kontrolleri).

### 6. Çok dillilik
`texts.text(key)` çağır, çeviriyi `assets/lang/*.json`'a yaz. Yeni dil: `en.json` kopyala → `_name` alanını ayarla → `FLAG_FOR_LANGUAGE` (icons.py) ekle.

### 7. Tema
`theme.py` — `apply_theme(app, name)` stylesheet üretir/uygular, `colour(name)` renk verir. `redress(root)` temaya göre ikonları yeniden boyar. Chart/pie renkleri `slice_colours()`'dan.

### 8. Arka plan işleri
`covers.py` — `QThreadPool` + `QRunnable` (`COVER_THREADS=4`). Thread içinde asla istisna kaçmaz (PyQt'te qFatal olur). Kapaklar bellekte önbellenir (`_images`), her grid yenilemesinde yeniden istenmez.

### 9. Sayfa yönetimi (app.py)
- `QStackedWidget`; 5 kalıcı sayfa + kitap detay sayfası dinamik eklenir/çıkarılır
- Dil değişince `_build_shell()` tüm sayfaları yeniden kurar (labels yeniden çevrilir); veri nesneleri (`library`, `ledger`, `goals`) pencerede yaşar

### 10. Sinyaller
Sayfalar arası iletişim `pyqtSignal` ile: `book_added`, `book_opened`, `book_edited`, `book.deleted`, `theme_changed`, `folder_changed`, `language_changed`, `covers.loaded`.

## Kod stili
- Fonksiyonlar, sınıflar ve hatta veri akışı için açıklayıcı **docstring'ler** (hangi sorunu çözdüğünü anlatır)
- Değişken/fonksiyon adları konuşma İngilizcesi, kısa ve betimleyici
- `#` yorumları neden'i açıklar, kod yorumlanmaz
- Tüm dosyalarda GPLv3 başlığı vardır — yeni dosya oluştururken kopyala
