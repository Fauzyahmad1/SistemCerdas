# ml/bersihkan_data.py
# Tugas: membaca data mentah, membersihkannya, lalu menyimpan data bersih.
# Cara menjalankan (dari folder utama proyek):  python ml/bersihkan_data.py

from pathlib import Path   # untuk menyusun alamat file dengan aman
import pandas as pd        # library tabel data

BASE = Path(__file__).resolve().parent.parent      # folder utama proyek
FILE_MENTAH = BASE / "data" / "motor_bekas_mentah.csv"
FILE_BERSIH = BASE / "data" / "motor_bekas.csv"

df = pd.read_csv(FILE_MENTAH)                      # baca data mentah
print("Baris awal                    :", len(df))

# Langkah 1: buang iklan yang harganya kemungkinan hanya uang muka (DP)
df = df[df["Is_DP_Clickbait"] == False]
print("Setelah buang iklan DP        :", len(df))

# Langkah 2: buang merek motor besar/premium (pasarnya berbeda, sampel sedikit)
MEREK_DIBUANG = ["Harley-Davidson", "BMW Motorrad", "Royal Enfield", "KTM"]
df = df[~df["Matched_Brand"].isin(MEREK_DIBUANG)]
print("Setelah buang merek premium   :", len(df))

# Langkah 3: ambil kolom yang dipakai saja, lalu ganti namanya
df = df[["Matched_Brand", "Matched_Model", "Claimed_Year", "Odometer_KM",
         "Tax_Status", "Seller_Type", "Price"]]
df.columns = ["merek", "model", "tahun", "km", "status_pajak", "jenis_penjual", "harga"]

# Langkah 4: buang baris tidak wajar dan duplikat
df = df[(df["km"] >= 0) & (df["harga"] >= 1_000_000)]
df = df.drop_duplicates()
print("Setelah buang duplikat/aneh   :", len(df))

# Langkah 5b: buang outlier harga per merek+model+tahun (metode IQR 1.5x) menggunakan transform agar kolom tidak hilang
def hitung_mask_iqr(s):
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    return (s >= q1 - 1.5 * iqr) & (s <= q3 + 1.5 * iqr)

mask_valid = df.groupby(["merek", "model", "tahun"])["harga"].transform(hitung_mask_iqr)
df = df[mask_valid].reset_index(drop=True)
print("Setelah buang outlier harga   :", len(df))

# Langkah 5: ubah harga ke satuan juta Rupiah agar angkanya mudah dibaca
df["harga"] = (df["harga"] / 1_000_000).round(2)

df.to_csv(FILE_BERSIH, index=False)                # simpan data bersih
print("\nData bersih disimpan di:", FILE_BERSIH)
print(df.describe().round(1))
