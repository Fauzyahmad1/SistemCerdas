# ekspedisi/services/ml.py
# Modul layanan machine learning: memuat model, metrik, melakukan prediksi, dan menyiapkan data grafik.

import json
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PATH_MODEL = BASE_DIR / "ml" / "model_harga.joblib"
PATH_METRIK = BASE_DIR / "ml" / "metrik.json"
PATH_DATA_BERSIH = BASE_DIR / "data" / "motor_bekas.csv"

# Variabel cache dalam memori agar tidak membaca file berulang-ulang
_model_cache = None
_metrik_cache = None
_grafik_cache = None


def muat_metrik():
    """Membaca file ml/metrik.json dan menyimpannya dalam cache."""
    global _metrik_cache
    if _metrik_cache is not None:
        return _metrik_cache

    if PATH_METRIK.exists():
        with open(PATH_METRIK, "r", encoding="utf-8") as f:
            _metrik_cache = json.load(f)
            return _metrik_cache

    # Fallback jika file metrik belum ada
    return {
        "model_terpakai": "Random Forest",
        "jumlah_data": 0,
        "jumlah_latih": 0,
        "jumlah_uji": 0,
        "hasil": {},
        "pilihan_model": {},
        "rentang_tahun": [2012, 2026],
        "status_pajak": ["Hidup / Panjang", "Mati / Off", "Unknown"],
        "jenis_penjual": ["Dealer", "Individual"]
    }


def muat_model():
    """Memuat pipeline model harga dari ml/model_harga.joblib."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if PATH_MODEL.exists():
        _model_cache = joblib.load(PATH_MODEL)
        return _model_cache
    return None


def prediksi_harga(merek, model_motor, tahun, km, status_pajak, jenis_penjual):
    """
    Memprediksi harga motor bekas dalam satuan juta Rupiah.
    Menggunakan Pipeline yang membungkus ColumnTransformer + Regressor.
    """
    model = muat_model()
    if model is None:
        raise ValueError("File model ML (model_harga.joblib) belum ditemukan.")

    # Susun input ke dalam DataFrame dengan struktur kolom yang persis sama dengan saat pelatihan
    data_input = pd.DataFrame([{
        "merek": str(merek),
        "model": str(model_motor),
        "tahun": int(tahun),
        "km": float(km),
        "status_pajak": str(status_pajak),
        "jenis_penjual": str(jenis_penjual)
    }])

    # Lakukan prediksi
    hasil = model.predict(data_input)[0]
    
    # Harga tidak boleh bernilai negatif
    harga_juta = max(0.5, round(float(hasil), 2))
    return harga_juta


def ambil_data_grafik():
    """
    Menyiapkan data agregat untuk 4 grafik Chart.js dari data/motor_bekas.csv:
    1. Harga rata-rata vs Tahun
    2. Harga rata-rata per Merek
    3. Hubungan Jarak Tempuh (KM) vs Harga
    4. Perbandingan Prediksi vs Harga Asli (sampel data uji)
    """
    global _grafik_cache
    if _grafik_cache is not None:
        return _grafik_cache

    if not PATH_DATA_BERSIH.exists():
        return {}

    df = pd.read_csv(PATH_DATA_BERSIH)

    # 1. Tren Harga Rata-Rata per Tahun
    rata_tahun = df.groupby("tahun")["harga"].mean().round(2).reset_index()
    grafik_tahun = {
        "labels": rata_tahun["tahun"].astype(str).tolist(),
        "values": rata_tahun["harga"].tolist()
    }

    # 2. Harga Rata-Rata per Merek (diurutkan dari tertinggi ke terendah)
    rata_merek = df.groupby("merek")["harga"].mean().round(2).sort_values(ascending=False).reset_index()
    grafik_merek = {
        "labels": rata_merek["merek"].tolist(),
        "values": rata_merek["harga"].tolist()
    }

    # 3. Hubungan Kilometer vs Harga (dikelompokkan per rentang km 10.000 agar grafik bersih dan informatif)
    bins_km = [0, 10000, 20000, 35000, 50000, 75000, 100000, 200000]
    labels_km = ["0-10rb", "10-20rb", "20-35rb", "35-50rb", "50-75rb", "75-100rb", ">100rb"]
    df["rentang_km"] = pd.cut(df["km"], bins=bins_km, labels=labels_km, include_lowest=True)
    rata_km = df.groupby("rentang_km", observed=False)["harga"].mean().round(2).reset_index()
    grafik_km = {
        "labels": rata_km["rentang_km"].astype(str).tolist(),
        "values": rata_km["harga"].fillna(0).tolist()
    }

    # 4. Prediksi vs Harga Asli (ambil sampel 35 motor acak dengan seed tetap agar konsisten)
    model = muat_model()
    if model is not None:
        sampel = df.sample(n=min(35, len(df)), random_state=42).copy()
        kolom_fitur = ["merek", "model", "tahun", "km", "status_pajak", "jenis_penjual"]
        sampel["harga_prediksi"] = model.predict(sampel[kolom_fitur]).round(2)
        grafik_prediksi_asli = {
            "labels": [f"{row['merek']} {row['model'][:10]} ({int(row['tahun'])})" for _, row in sampel.iterrows()],
            "asli": sampel["harga"].tolist(),
            "prediksi": sampel["harga_prediksi"].tolist()
        }
    else:
        grafik_prediksi_asli = {"labels": [], "asli": [], "prediksi": []}

    _grafik_cache = {
        "tahun": grafik_tahun,
        "merek": grafik_merek,
        "km": grafik_km,
        "prediksi_vs_asli": grafik_prediksi_asli
    }
    return _grafik_cache
