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

# Langkah 5: ubah harga ke satuan juta Rupiah agar angkanya mudah dibaca
df["harga"] = (df["harga"] / 1_000_000).round(2)

df.to_csv(FILE_BERSIH, index=False)                # simpan data bersih
print("\nData bersih disimpan di:", FILE_BERSIH)
print(df.describe().round(1))
