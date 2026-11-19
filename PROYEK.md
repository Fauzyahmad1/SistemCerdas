# PROYEK: Prediksi Harga Motor Bekas (Django + ML + AI + Firebase)

Tugas Mata Kuliah Sistem Cerdas, Politeknik Negeri Madiun. Pengembangan Modul 14 (aplikasi berbasis Django, bukan Streamlit).
Pemilik: Fauzy Ahmad Muzayyin, NIM 253307024, Kelas 3A.

---

## 1. Ringkasan

Aplikasi web lokal berbasis Django yang memperkirakan harga motor bekas dari merek, model, tahun, kilometer, status pajak, dan jenis penjual. Hasil prediksi disimpan ke Firebase Firestore dan ditampilkan sebagai riwayat. Aplikasi juga punya grafik data, chatbot FAQ jual-beli motor bekas (AI), dan penjelasan hasil prediksi oleh AI.

## 2. Empat syarat yang WAJIB ada

| Syarat | Wujud di aplikasi |
|---|---|
| Grafik | Halaman Grafik: harga vs tahun, harga rata-rata per merek, harga vs kilometer, prediksi vs harga asli |
| Machine learning | Regresi (LinearRegression) + pembanding RandomForestRegressor, dievaluasi dengan data uji |
| Pemanfaatan AI | Chatbot FAQ (RAG mini) + tombol "Jelaskan hasil" oleh LLM, dengan fallback |
| Aplikasi jadi | Berjalan lokal lewat `python manage.py runserver`, 4 halaman, tanpa error |
| (Tambahan) Firebase | Riwayat prediksi disimpan di Firestore |

## 3. Dataset

- Sumber: repo `Mufti129/motor-price-id` (https://github.com/Mufti129/motor-price-id), file `dataset_mentah.csv`, 17.000 baris, harga dalam Rupiah. Repo ini tidak mencantumkan lisensi.
- **PERINGATAN JUJUR:** hasil pemeriksaan menunjukkan data ini kemungkinan besar **dibuat generator, bukan iklan nyata**: semua `External_ID` berawalan `gen_`, tiap merek tepat 1.000 baris, kolom URL berisi tautan pencarian, dan deskripsi berpola template. Wajib ditulis di README dan Beranda: "Data motor bekas Indonesia yang tampaknya dibuat generator (sumber: repo Mufti129). Bukan harga pasar sebenarnya."
- Simpan sebagai `data/motor_bekas_mentah.csv`. Hasil pembersihan disimpan di `data/motor_bekas.csv` oleh `ml/bersihkan_data.py`.

**Kolom yang dipakai (nama asli lalu nama baru):**

| Asli | Baru | Keterangan |
|---|---|---|
| Matched_Brand | merek | kategori |
| Matched_Model | model | kategori (140 model) |
| Claimed_Year | tahun | angka |
| Odometer_KM | km | angka |
| Tax_Status | status_pajak | Hidup / Panjang, Mati / Off, Unknown |
| Seller_Type | jenis_penjual | Individual / Dealer |
| Price | harga | target, Rupiah |

**Kolom yang dibuang:** ID, Source, External_ID, URL, Title, Raw_Description, Plate_Region, Province, City, Has_BPKB, Has_STNK (semuanya True, tidak informatif), Matched_Variant (terlalu banyak kategori, 367).

**Aturan pembersihan (`ml/bersihkan_data.py`, cetak jumlah baris tiap langkah):**
1. Buang baris `Is_DP_Clickbait == True` (harga di iklan itu kemungkinan uang muka, bukan harga penuh).
2. Buang merek motor besar/premium yang harganya jauh berbeda: Harley-Davidson, BMW Motorrad, Royal Enfield, KTM. Alasan ditulis di README (pasar berbeda, sampel kecil, bisa merusak regresi).
3. Buang duplikat dan baris tidak wajar (km di bawah 0, harga di bawah Rp1 juta).
4. Ubah `harga` ke satuan juta Rupiah (bagi 1.000.000). Tulis satuan di aplikasi.
5. Jangan memakai kolom teks bebas dan jangan menyimpan data pribadi.

**Catatan analisis (isi di README):** `tahun` dan `km` berkorelasi sangat kuat (sekitar -0,95), sehingga koefisien regresi linear bisa tidak stabil. Itu salah satu alasan RandomForest dipakai sebagai pembanding.

## 4. Pengembangan dari notebook yang dipakai

Hanya notebook milik sendiri yang dipakai. Jangan memakai P07 (milik Angga Dwi Saputro).

| Notebook | Yang dipakai | Di aplikasi menjadi |
|---|---|---|
| P09 (regresi) | `LinearRegression`, fitur banyak kolom, mengubah teks ya/tidak menjadi angka 1/0, garis regresi, fungsi `tanya_ai(judul, isi)` | Model harga, encoding kolom kategori, grafik regresi, penjelasan grafik oleh AI |
| P10 (evaluasi) | Pembagian data latih/uji, metrik, cara membaca hasil evaluasi jujur | `train_test_split`, MAE, RMSE, R2 di halaman Prediksi, plus catatan overfitting |
| P13 (chatbot RAG) | `bersihkan`, `SINONIM`, `cari_faq`, `rag_kos`, `tanya_llm` dengan coba ulang, jawaban jujur "tidak tahu" | Chatbot FAQ motor bekas |
| P11 (prompt) | Pola prompt peran + konteks + batasan + format, aturan penggunaan AI | Prompt chatbot dan prompt penjelasan hasil |

Tambahan di luar notebook (hanya sebagai pembanding, jelaskan alasannya di README): `RandomForestRegressor`.

Tidak dipakai: P04, P05, P06, P11 (algoritma genetika), P12.

## 5. Struktur proyek

```
proyek_ekspedisi/        (folder proyek)
├── manage.py
├── config/              settings.py, urls.py
├── ekspedisi/           app utama
│   ├── views.py
│   ├── urls.py
│   └── services/
│       ├── ml.py        muat model, prediksi
│       ├── ai.py        tanya_llm + fallback
│       ├── faq.py       data FAQ + cari_faq (RAG mini)
│       └── firebase.py  simpan dan baca riwayat
├── ml/
│   ├── bersihkan_data.py  mentah -> bersih
│   ├── latih_model.py     latih dan simpan model + metrik
│   ├── model_harga.joblib
│   └── metrik.json
├── data/            motor_bekas_mentah.csv, motor_bekas.csv
├── templates/           base.html, beranda.html, prediksi.html, grafik.html, chatbot.html, riwayat.html
├── static/css/style.css
├── .env                 JANGAN diunggah
├── .env.example
├── .gitignore           isi: venv/, .env, firebase-key.json, __pycache__/, db.sqlite3
├── requirements.txt
└── README.md
```

## 6. Halaman dan perilaku

1. **Beranda**: ringkasan, jumlah data, metrik model utama, label sumber data, tombol ke halaman lain.
2. **Prediksi**: form (merek, model, tahun, km, status pajak, jenis penjual; pilihan model menyesuaikan merek) lalu hasil harga dalam juta Rupiah. Tampilkan metrik evaluasi dan catatan "perkiraan, bukan harga pasti". Setelah prediksi, simpan ke Firebase. Tombol "Jelaskan hasil" memanggil AI.
3. **Grafik**: Chart.js (CDN, versi dipin). Grafik yang ditampilkan ada di bagian 2.
4. **Chatbot**: tanya jawab FAQ jual-beli motor bekas.
5. **Riwayat**: tabel prediksi terakhir dari Firebase (misalnya 20 terakhir). Jika Firebase tidak terhubung, tampilkan pesan jelas, jangan error.

## 7. Spesifikasi machine learning

- Target: `harga` (juta Rupiah). Fitur: `merek`, `model`, `tahun`, `km`, `status_pajak`, `jenis_penjual`.
- Kolom kategori (`merek`, `model`, `status_pajak`, `jenis_penjual`) diubah dengan one-hot encoding lewat `pd.get_dummies` atau `OneHotEncoder`. Pakai Pipeline agar kolom input saat prediksi PERSIS sama dengan saat latih (pelajaran P-modul: kolom input harus sama).
- Bagi data 80/20, `random_state=42`.
- Latih dua model: `LinearRegression` dan `RandomForestRegressor(n_estimators=100, random_state=42)`.
- Hitung MAE, RMSE, R2 untuk keduanya pada data uji. Simpan di `ml/metrik.json`. Model yang dipakai aplikasi = model dengan MAE terendah.
- Simpan dengan `joblib`.
- Tampilkan di halaman bahwa skor latih jauh lebih tinggi dari skor uji berarti overfitting.
- Semua angka metrik dihitung dari data, tidak boleh ditulis manual.

## 8. Spesifikasi AI (Google Gemini REST API Langsung)

**Koneksi:** Google Gemini REST API langsung memakai library `requests`.
- `POST` JSON ke `https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent`
- Header: `"x-goog-api-key: {GEMINI_API_KEY}"`, `"Content-Type": "application/json"`
- Body: `{"contents":[{"parts":[{"text": prompt}]}]}`
- Teks jawaban diekstrak dari: `respon["candidates"][0]["content"]["parts"][0]["text"]`
- `GEMINI_API_KEY` dan `GEMINI_MODEL` dibaca dari `.env` lewat `python-dotenv`. Dilarang menulis, mencetak, atau mencatat nilai key di kode, log, README, atau output. Ganti `.env.example` menjadi `GEMINI_API_KEY=`, `GEMINI_MODEL=`, `FIREBASE_KEY_PATH=firebase-key.json`.
- Timeout 30 detik. Coba ulang maksimal 3 kali dengan jeda 2, 4, 6 detik HANYA untuk error sementara (503 atau 429). Untuk error 400/401/403 jangan diulang.

**Chatbot (RAG mini):** bersihkan teks, ganti sinonim, ambil 2 entri FAQ teratas, sisipkan sebagai konteks, LLM menjawab maksimal 2 kalimat HANYA dari FAQ. Jika tidak ada entri relevan, jawab "Maaf, informasi itu belum ada di FAQ resmi. Silakan hubungi penjual." tanpa memanggil LLM.
- 8 entri FAQ: cek surat kendaraan (STNK/BPKB), pajak, balik nama, cek kondisi mesin, faktor penurun harga, tips tawar-menawar, uji jalan, dokumen yang disiapkan.

**Penjelasan hasil:** kirim angka prediksi dan input ke LLM, minta penjelasan singkat (2 sampai 3 kalimat) memakai pola prompt peran + konteks + batasan + format. Larangan: AI tidak boleh mengarang angka di luar yang diberikan.

**Fallback WAJIB:** jika Gemini gagal atau key kosong, chatbot menampilkan FAQ teratas dengan label "(AI sedang tidak tersedia)" dan penjelasan hasil memakai teks otomatis dari angka.

## 9. Firebase (Firestore)

Aplikasi memakai Firestore lewat server (Django), bukan langsung dari browser.

**Koleksi `prediksi_motor`** (satu dokumen per prediksi, ID otomatis):

| Field | Tipe | Isi |
|---|---|---|
| merek | string | contoh "Honda" |
| model | string | contoh "PCX" |
| tahun | number | tahun produksi |
| km | number | kilometer |
| status_pajak | string | Hidup / Panjang, Mati / Off, Unknown |
| jenis_penjual | string | Individual / Dealer |
| harga_prediksi | number | hasil model (juta Rupiah) |
| model_ml | string | nama model (Linear Regression / Random Forest) |
| dibuat_pada | timestamp | waktu prediksi (server timestamp) |

Aturan:
- Jangan menyimpan data pribadi pengguna (nama, IP, email). Riwayat cukup berupa input motor dan hasilnya.
- Kunci akun layanan (`firebase-key.json`) TIDAK BOLEH ada di repo. Path-nya dibaca dari `.env` (`FIREBASE_KEY_PATH`).
- Jika Firebase gagal (kunci salah, tidak ada internet), prediksi tetap tampil. Simpan dibungkus `try/except`, dan tampilkan peringatan kecil "riwayat tidak tersimpan".
- Batasi pembacaan riwayat (`limit(20)` urut `dibuat_pada` menurun).

## 10. Aturan kode dan etika (kontrak kuliah)

- Kode sederhana dan bisa dijelaskan baris per baris. Komentar bahasa Indonesia di bagian penting. Hindari abstraksi berlebihan.
- Memakai AI untuk menjelaskan konsep dan mencari kesalahan, bukan untuk membuat semuanya dari nol tanpa dipahami.
- Tidak memasukkan data pribadi (NIK, alamat, data mahasiswa lain) ke layanan AI.
- API key/token kosongkan sebelum file dikumpulkan. Kunci hanya ada di `.env` lokal.
- Jawaban AI untuk fakta (harga, aturan pajak, dokumen) tidak dianggap pasti. Beri catatan agar pengguna memeriksa ke sumber resmi.
- Tidak membuat data atau metrik palsu.
- Hasil prediksi adalah perkiraan, bukan nilai taksiran resmi.

## 11. Desain tampilan

Gaya dashboard terang: sidebar kiri biru indigo dengan menu aktif berbentuk tab putih, topbar dengan pencarian, konten berupa kartu putih bersudut membulat dan bayangan halus. Warna utama indigo (sekitar #4C63D2), tipografi Inter, angka metrik besar dan tebal. Responsif untuk layar kecil.

## 12. Lingkungan

Windows, VS Code, Python 3.15, venv. Paket: `django pandas scikit-learn joblib requests python-dotenv firebase-admin`.

## 13. Checklist selesai

- [x] `python manage.py check` tanpa error
- [x] `python ml/bersihkan_data.py` menghasilkan `data/motor_bekas.csv`
- [x] `python ml/latih_model.py` menghasilkan `model_harga.joblib` dan `metrik.json`
- [x] Prediksi tampil dan tersimpan di Firestore
- [x] Halaman Riwayat membaca dari Firestore
- [x] Empat grafik tampil
- [x] Chatbot menjawab dan fallback bekerja saat AI dimatikan
- [x] Aplikasi tetap jalan saat Firebase dimatikan
- [x] `.env` dan `firebase-key.json` tidak ikut terkumpul
- [x] README berisi deskripsi, cara menjalankan, sumber data, keterbatasan, pembagian tugas
