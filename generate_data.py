"""
Sentetik Talep Verisi Üretimi
================================
Bu script, gerçek bir gıda üretim şirketinin (Dardanel benzeri) çoklu ürün
talep verisini simüle eder. Gerçekçi olması için:
  - Trend (yıllar içinde büyüme)
  - Haftalık mevsimsellik (hafta sonu etkisi)
  - Yıllık mevsimsellik (Ramazan öncesi stoklama, yaz aylarında salata/konserve talebi)
  - Promosyon etkisi
  - Resmi tatil etkisi
  - Fiyat değişkenliği
  - Kasıtlı eksik veri (%3) ve aykırı değer (%1.5) enjeksiyonu
içerir. NOT: Bu veri gerçek Dardanel verisi DEĞİLDİR; halka açık gerçek veri
setine erişim (internet) mümkün olmadığı için, projenin metodolojisini gerçek
bir üretim/talep senaryosu üzerinde göstermek amacıyla kontrollü şekilde
üretilmiştir. Proje raporunda bu durum açıkça belirtilecektir (Bölüm 6'da
kısıt olarak da tekrar vurgulanacak).
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

# ---------------------------------------------------------------
# 1. Zaman aralığı ve ürünler
# ---------------------------------------------------------------
start_date = "2022-01-01"
end_date = "2024-12-31"
dates = pd.date_range(start_date, end_date, freq="D")
n_days = len(dates)

products = {
    "TON80":  {"name": "Ton Balığı Konservesi 80g",  "base": 850, "trend": 0.35, "price": 28.0,  "yaz_katsayisi": 1.35, "ramazan_katsayisi": 1.20},
    "TON160": {"name": "Ton Balığı Konservesi 160g", "base": 520, "trend": 0.25, "price": 48.0,  "yaz_katsayisi": 1.30, "ramazan_katsayisi": 1.25},
    "SARDL":  {"name": "Sardalya Konservesi",        "base": 410, "trend": 0.15, "price": 22.5,  "yaz_katsayisi": 1.45, "ramazan_katsayisi": 1.10},
    "SOMON":  {"name": "Somon Konservesi",           "base": 180, "trend": 0.45, "price": 65.0,  "yaz_katsayisi": 1.15, "ramazan_katsayisi": 1.30},
    "ZEYTY":  {"name": "Zeytinyağı 1L",               "base": 300, "trend": 0.20, "price": 210.0, "yaz_katsayisi": 1.05, "ramazan_katsayisi": 1.55},
}

# Yaklaşık Ramazan Bayramı başlangıç tarihleri (2022-2024) - basitleştirilmiş
ramazan_bayrami = {
    2022: pd.Timestamp("2022-05-02"),
    2023: pd.Timestamp("2023-04-21"),
    2024: pd.Timestamp("2024-04-10"),
}
kurban_bayrami = {
    2022: pd.Timestamp("2022-07-09"),
    2023: pd.Timestamp("2023-06-28"),
    2024: pd.Timestamp("2024-06-16"),
}

# Diğer sabit resmi tatiller (ay, gün)
sabit_tatiller = [(1, 1), (4, 23), (5, 1), (5, 19), (8, 30), (10, 29)]


def is_near_ramazan(d):
    y = d.year
    if y not in ramazan_bayrami:
        return 0
    bayram = ramazan_bayrami[y]
    delta = (bayram - d).days
    return 1 if 0 <= delta <= 10 else 0  # bayram öncesi 10 gün stoklama etkisi


def is_holiday(d):
    if (d.month, d.day) in sabit_tatiller:
        return 1
    for by in [ramazan_bayrami, kurban_bayrami]:
        if d.year in by:
            bayram = by[d.year]
            if bayram <= d <= bayram + pd.Timedelta(days=3):
                return 1
    return 0


rows = []
for sku, info in products.items():
    # Promosyon günlerini rastgele seç (yaklaşık ayda 2 gün, ürüne özel)
    promo_days = set(np.random.choice(dates, size=int(n_days * 0.06), replace=False))

    for i, d in enumerate(dates):
        # Trend (yıllık büyüme, günlük küçük artış)
        trend_component = info["trend"] * (i / 30.0)

        # Haftalık mevsimsellik: hafta sonu (Cumartesi=5, Pazar=6) talebi daha düşük
        # (market/perakende sevkiyatı hafta içi yoğun, market rafına yerleşim hafta içi)
        weekday = d.weekday()
        haftalik_katsayi = 0.75 if weekday >= 5 else 1.05

        # Yıllık mevsimsellik: yaz ayları (haziran-ağustos) + ramazan öncesi
        yaz_etkisi = info["yaz_katsayisi"] if d.month in [6, 7, 8] else 1.0
        ramazan_etkisi = info["ramazan_katsayisi"] if is_near_ramazan(d) else 1.0

        # Promosyon etkisi
        promo = 1 if d in promo_days else 0
        promo_etkisi = 1.35 if promo else 1.0

        # Resmi tatil (sevkiyat/üretim tatili -> talep kaydı düşük görünür)
        tatil = is_holiday(d)
        tatil_etkisi = 0.4 if tatil else 1.0

        # Fiyat: küçük rastgele oynama + yıllık enflasyon etkisi
        fiyat = info["price"] * (1 + 0.12 * (i / 365.0)) * np.random.normal(1.0, 0.02)

        # Temel talep hesaplama
        base_demand = (info["base"] + trend_component) * haftalik_katsayi * yaz_etkisi \
                      * ramazan_etkisi * promo_etkisi * tatil_etkisi

        # Gürültü (Poisson benzeri doğal varyasyon)
        noise = np.random.normal(0, base_demand * 0.08)
        talep = max(0, base_demand + noise)

        rows.append({
            "tarih": d,
            "urun_kodu": sku,
            "urun_adi": info["name"],
            "satis_adedi": round(talep),
            "birim_fiyat": round(fiyat, 2),
            "promosyon_var_mi": promo,
            "resmi_tatil_mi": tatil,
        })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------
# 2. Kasıtlı veri kalitesi sorunları ekleme (gerçekçilik için)
# ---------------------------------------------------------------
# %3 oranında eksik satış verisi (örn. ERP kayıt hatası / senkronizasyon sorunu)
missing_idx = df.sample(frac=0.03, random_state=1).index
df.loc[missing_idx, "satis_adedi"] = np.nan

# %1.5 oranında aykırı değer (örn. toplu ihracat siparişi ya da veri giriş hatası)
outlier_idx = df.sample(frac=0.015, random_state=2).index
outlier_type = np.random.choice(["spike", "error"], size=len(outlier_idx))
for idx, otype in zip(outlier_idx, outlier_type):
    if otype == "spike":
        df.loc[idx, "satis_adedi"] = df.loc[idx, "satis_adedi"] * np.random.uniform(4, 7)
    else:
        df.loc[idx, "satis_adedi"] = df.loc[idx, "satis_adedi"] * 0.02  # veri giriş hatası (çok düşük)

# Birkaç satırda birim fiyat eksik bırak (%0.5)
price_missing_idx = df.sample(frac=0.005, random_state=3).index
df.loc[price_missing_idx, "birim_fiyat"] = np.nan

df = df.sort_values(["urun_kodu", "tarih"]).reset_index(drop=True)

out_path = Path(__file__).resolve().parent / "talep_verisi_ham.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"Kaydedildi: {out_path}")
print(f"Toplam satır: {len(df)}")
print(df.head(10))
print("\nEksik değer sayıları:\n", df.isna().sum())
