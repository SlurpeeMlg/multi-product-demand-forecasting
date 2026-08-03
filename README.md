# Gıda Üretiminde Çoklu Ürün Talep Tahmini

Bu proje, beş gıda ürünü için günlük talebi tahmin eder ve tahminleri örnek
emniyet stoğu / yeniden sipariş noktası önerilerine dönüştürür. Çalışma;
problem tanımı, veri temizleme, EDA, özellik mühendisliği, zaman serisi çapraz
doğrulaması, model karşılaştırma, hiperparametre optimizasyonu,
yorumlanabilirlik ve iş önerilerini tek notebook içinde içerir.

## Dosyalar

- `proje.ipynb`: Ana analiz, açıklamalar, grafikler ve modelleme
- `talep_verisi_ham.csv`: 5 ürün × 3 yıl günlük sentetik veri
- `generate_data.py`: Ham sentetik veriyi aynı rastgelelik tohumu ile üretir
- `requirements.txt`: Gerekli Python paketleri
- `outputs/`: Notebook çalıştığında grafik, tablo, tahmin ve model çıktıları

## Çalıştırma

Python 3.11 veya üzeri önerilir.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
jupyter lab proje.ipynb
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab proje.ipynb
```

Notebook'ta **Run All** çalıştırıldığında temiz veri, özellikli veri, grafikler,
model karşılaştırma tabloları, test tahminleri, stok önerileri ve eğitilmiş
`joblib` modeli ham CSV'nin yanındaki `outputs/` klasörüne yazılır.

## Yöntem Özeti

- Eksik satış ve fiyatlar ürün bazında zaman sıralı interpolasyonla doldurulur.
- Aykırı talep değerleri ürün bazında IQR sınırlarına çekilir.
- Takvim, fiyat endeksi, lag ve hareketli pencere özellikleri türetilir.
- Son üç ay dokunulmamış test dönemi olarak ayrılır.
- Rastgele K-Fold yerine tarih bazlı `TimeSeriesSplit` kullanılır.
- Ridge, Random Forest ve Gradient Boosting modelleri karşılaştırılır.
- Final Gradient Boosting modeli `RandomizedSearchCV` ile optimize edilir.
- Feature importance, permutation importance, yerel karşı-olgusal açıklama ve
  isteğe bağlı SHAP waterfall grafiği sunulur.

## Önemli Kısıt

Veri gerçek şirket verisi değildir. Stajda gözlemlenen üretim-planlama
dinamiklerini göstermek amacıyla kontrollü biçimde üretilmiş sentetik veridir;
sonuçlar herhangi bir şirketin gerçek satış performansı olarak yorumlanamaz.
