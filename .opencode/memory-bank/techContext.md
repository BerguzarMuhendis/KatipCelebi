# Tech Context

## Teknoloji yığını
- **Python 3** (sürüm üst sınırı yok, tip ipuçları kullanılıyor: `Book | None`, `list[str]`)
- **PyQt6** (>= 6.5) — masaüstü arayüz
- **PyQt6-Charts** (>= 6.5) — istatistik grafikleri
- **openpyxl** (>= 3.1) — Excel dışa/geri aktarım
- **materialyoucolor** (>= 3.0) — Material Design 3 renk motoru (MIT, GPLv3 uyumlu)
- **keyring** (>= 24) — Open Library giriş bilgisi OS kimlik deposunda (dosyada asla)

## Bağımlılıkların kurulumu
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python src/app.py
```
Adwaita temaları için Linux'ta sistem paketi gerekir (`adwaita-qt6`); yoksa Fusion stiliyle geri düşer.

## Proje dizin yapısı
```
KatipCelebi-main/
├── src/                # tüm kaynak
├── assets/
│   ├── icons/          # Material Symbols SVG'leri (Apache 2.0)
│   ├── lang/           # en, tr, ru, zh, es, fr JSON dosyaları
│   └── styles/         # default.qss (custom tema şablonu)
├── KatipCelebi.spec    # PyInstaller yapılandırması
├── requirements.txt
├── CONTRIBUTING.md
├── LICENSE-GPLV3
└── LICENSE-APACHE
```

## Paketleme
```powershell
pip install pyinstaller
pyinstaller KatipCelebi.spec
```
Spec dosyası `--add-data`, `--name`, `--windowed`, `--icon` bayraklarını gerekli kılmaz. `assets/` PyInstaller'da `sys._MEIPASS`'tan bulunur (`shared/paths.py`).

## Veri konumları
| Veri | Konum |
|---|---|
| Kütüphane/kişiler/ödünçler/hedefler | Kullanıcının seçtiği klasör (`library.json`, `people.json`, `loans.json`, `goals.json`) |
| Ayarlar | `%APPDATA%/KatipCelebi/settings.json` (Win) / `~/.config/KatipCelebi` (Linux) |
| Kapak önbelleği | `%APPDATA%/KatipCelebi/covers/<isbn>_<M|L>.jpg` |
| Log | kütüphane klasöründe `katipcelebi.log` |

## Ağ servisleri
- **Open Library** (`openlibrary.org`): ISBN sorgusu, kapaklar (`covers.openlibrary.org`), `/api/import` ile kitap katkılama. User-Agent tanımlı. 10s timeout.
- Kapaklar Open Library'den indirilir; çeşitli boyutlar: `M` (thumb), `L` (large).

## Platform notları
- Windows: `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID` ile görev çubuğu ikonu
- HiDPI: `QApplication.setHighDpiScaleFactorRoundingPolicy(PassThrough)` ve kapak/placeholder'lar `_device_ratio()` ile fiziksel pikselde çizilir
- Windows'ta `_fsync_dir` desteklenmez (sessizce geçer)

## Önemli sabitler
- `SIDEBAR_WIDTH = 220` (app.py)
- `COVER_THREADS = 4`, `THUMB_SIZE = (150, 210)`, `LARGE_SIZE = (260, 380)` (covers.py)
- `MAX_IMPORT_BYTES = 20 MiB` (excel.py)
- `MAX_COPIES = 999` (model.py)
- `MAX_SUBJECT_TAGS = 6` (tags.py)
- `USER_AGENT = "KatipCelebi/2.0 (...)"` (openlibrary.py)

## Test durumu
Projede şu an test dosyası bulunmuyor. `texts.py` ve `covers.py` test varsayımıyla yazılmış (testlerin varlığına göndermeler var), ama repoda test yok.

## Lisans uyumluluğu
GPLv3 kaynak + Apache 2.0 varlıklar. Renk motoru (materialyoucolor) MIT, GPLv3 ile uyumlu olduğu yorumla belirtilmiş.
