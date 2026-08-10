# Product Context

## Neden var
İnsanların kitaplarını, kimlere ödünç verdiklerini ve okuma alışkanlıklarını tek bir yerde, yerel ve güvenli tutmak. Bulut hesabı istemeyen, verisi kullanıcının kendi seçtiği klasörde duran bir araç.

## Problemler ve yaklaşımlar

**Veri güvenliği en önemli prensiptir.** Kütüphane JSON dosyaları kullanıcının seçtiği klasörde tutulur. Yazma atomik (temp + rename + fsync) olduğundan çökme sırasında dosya asla yarım kalmaz. Okunamayan bir dosya "boş" olarak yorumlanmaz — önce güvenli bir `.bak` adına taşınır (`rescue_file`), kullanıcıya nereye gittiği söylenir.

**Bellek ve disk hep senkron.** Bir kitap ancak dosyaya yazma başarılı olursa listede kalır; başarısız yazma değişikliği geri alır. Eski sürümde başarısız kayıt, pencerenin dosyada olmayan kitap göstermesine yol açıyordu.

**Her faktör tek yerde yaşar.** "Bu kitap dışarıda mı?" ve "bu kişiye ne kadar güvenirim?" sorularının cevabı loans listesinden *hesaplanır*, ayrıca saklanmaz. İki yer aynı gerçeği tutarsa bir yer yanılır — ve yanılan hep okunan taraf olur.

**Boş mesajlar kullanıcıyı yanlış yönlendirir.** Okunamayan dosya sessizce boş sayılırsa kullanıcı kitaplarını kaybettiğini düşünür. Bu yüzden `_report_damage` kurtarılan dosyaların yerini söyler.

## Dil felsefesi
Kod `text("key")` ile çalışır; kelimeler `assets/lang/*.json` dosyalarından gelir. İngilizce temel dildir, eksik anahtar İngilizce'ye düşer. Yeni dil eklemek sadece JSON dosyası eklemektir — kod hiçbir dili adlandırmaz.

## Tema felsefesi
Her renk `theme.py`'de bir kez adlandırılır; renkler `palette.py`'de kullanıcının seçtiği tek bir seed'den Material Design 3 kurallarıyla türetilir. Hiçbir modül (grafikler, kapak yer tutucuları dahil) renkleri elle yazmaz.

## Kullanıcı arayüzü akışı
- İlk açılış: Welcome → Setup (dil, klasör, tema seçimi)
- Sonra: sol kenar çubuğundan 5 sayfa — Kitap Ekle, Kütüphane, Kişiler, İstatistikler, Ayarlar
- Bir kitaba tıklayınca aynı pencerede ayrı bir sayfada detay açılır; sidebar kilitlenir, Back düğmesi ile dönülür
- Dil değişince tüm sayfalar yeniden kurulur (`_build_shell`), veriler korunur
