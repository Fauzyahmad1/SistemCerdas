import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / "data" / "motor_bekas.csv")

def deteksi_outlier(group):
    Q1 = group["harga"].quantile(0.25)
    Q3 = group["harga"].quantile(0.75)
    IQR = Q3 - Q1
    batas_bawah = Q1 - 1.5 * IQR
    batas_atas  = Q3 + 1.5 * IQR
    return group[(group["harga"] < batas_bawah) | (group["harga"] > batas_atas)]

outlier = df.groupby(["merek", "model", "tahun"], group_keys=False).apply(deteksi_outlier)
print(f"Total baris    : {len(df)}")
print(f"Outlier harga  : {len(outlier)}")
print(f"Sisa setelah bersih: {len(df) - len(outlier)}")
print()
print(outlier.reset_index(drop=True).to_string(index=False))
