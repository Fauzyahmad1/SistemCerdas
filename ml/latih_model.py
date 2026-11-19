# ml/latih_model.py
# Tugas: melatih model prediksi harga motor bekas, mengevaluasinya, lalu menyimpannya.
# Cara menjalankan (dari folder utama proyek):  python ml/latih_model.py

import json                                   # menyimpan metrik ke file .json
from pathlib import Path
import joblib                                 # menyimpan model ke file
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer          # memperlakukan kolom dengan cara berbeda
from sklearn.preprocessing import OneHotEncoder        # mengubah teks kategori jadi angka 0/1
from sklearn.pipeline import Pipeline                  # menggabungkan persiapan data + model
from sklearn.model_selection import train_test_split   # membagi data latih dan data uji
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / "data" / "motor_bekas.csv")    # data hasil bersihkan_data.py

KOLOM_KATEGORI = ["merek", "model", "status_pajak", "jenis_penjual"]   # kolom teks
KOLOM_ANGKA = ["tahun", "km"]                                          # kolom angka
X = df[KOLOM_KATEGORI + KOLOM_ANGKA]     # fitur (penebak)
y = df["harga"]                          # target (yang ditebak), satuan juta Rp

# Bagi data: 80% untuk belajar, 20% untuk menguji (soal ujian yang disegel)
X_latih, X_uji, y_latih, y_uji = train_test_split(X, y, test_size=0.2, random_state=42)

def buat_pipeline(model):
    # kolom teks diubah ke 0/1; kolom angka dibiarkan apa adanya
    persiapan = ColumnTransformer([
        ("kategori", OneHotEncoder(handle_unknown="ignore"), KOLOM_KATEGORI),
    ], remainder="passthrough")
    return Pipeline([("persiapan", persiapan), ("model", model)])

kandidat = {
    "Regresi Linear": buat_pipeline(LinearRegression()),
    "Random Forest": buat_pipeline(RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
}

hasil = {}
for nama, pipa in kandidat.items():
    pipa.fit(X_latih, y_latih)                         # model belajar dari data latih
    tebak = pipa.predict(X_uji)                        # menebak data uji
    hasil[nama] = {
        "mae": round(float(mean_absolute_error(y_uji, tebak)), 2),               # rata-rata selisih (juta Rp)
        "rmse": round(float(np.sqrt(mean_squared_error(y_uji, tebak))), 2),      # selisih, hukuman lebih berat untuk kesalahan besar
        "r2_uji": round(float(r2_score(y_uji, tebak)), 3),                       # seberapa baik pada data uji
        "r2_latih": round(float(r2_score(y_latih, pipa.predict(X_latih))), 3),   # pada data latih (pembanding overfitting)
    }
    print(nama, hasil[nama])

terbaik = min(hasil, key=lambda n: hasil[n]["mae"])    # pilih model dengan MAE terkecil
print("\nModel terbaik:", terbaik)
joblib.dump(kandidat[terbaik], BASE / "ml" / "model_harga.joblib")   # simpan model terbaik

# Simpan juga metrik dan pilihan form (merek -> daftar model) untuk dipakai aplikasi
pilihan = {m: sorted(g["model"].unique().tolist()) for m, g in df.groupby("merek")}
metrik = {"model_terpakai": terbaik, "jumlah_data": int(len(df)),
          "jumlah_latih": int(len(X_latih)), "jumlah_uji": int(len(X_uji)), "hasil": hasil,
          "pilihan_model": pilihan,
          "rentang_tahun": [int(df["tahun"].min()), int(df["tahun"].max())],
          "status_pajak": sorted(df["status_pajak"].unique().tolist()),
          "jenis_penjual": sorted(df["jenis_penjual"].unique().tolist())}
(BASE / "ml" / "metrik.json").write_text(json.dumps(metrik, indent=2, ensure_ascii=False), encoding="utf-8")
print("Model dan metrik tersimpan di folder ml/")
