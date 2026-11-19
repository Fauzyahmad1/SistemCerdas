# MotoCerdas: Aplikasi Prediksi Harga Motor Bekas

Tugas Mata Kuliah Sistem Cerdas - Pengembangan Modul 14  
Program Studi Teknik Informatika, Politeknik Negeri Madiun  
**Pemilik Proyek:** Fauzy Ahmad Muzayyin (NIM: 253307024, Kelas: 3A)

---

## 1. Deskripsi Proyek

Aplikasi web berbasis **Django** yang mengintegrasikan model Machine Learning regresi untuk menaksir harga motor bekas di Indonesia. Aplikasi dilengkapi dengan sistem tanya-jawab FAQ berbasis RAG mini (AI), analisis visual data menggunakan Chart.js, serta pencatatan riwayat transaksi prediksi ke cloud database Google Firebase Firestore.

Aplikasi dirancang dengan arsitektur modular, tangguh (*fault-tolerant*), dan memiliki mekanisme *fallback* menyeluruh jika terjadi kendala pada layanan cloud eksternal (Google Gemini REST API maupun Firebase Firestore).

---

## 2. Empat Fitur Wajib & Fitur Tambahan

| Fitur | Deskripsi & Implementasi di Aplikasi |
|---|---|
| **1. Machine Learning** | Regresi Random Forest (`RandomForestRegressor`) dan Regresi Linear (`LinearRegression`) dengan pipeline `ColumnTransformer` + `OneHotEncoder` untuk memprediksi harga motor (juta Rupiah). |
| **2. Analisis Grafik** | Visualisasi analitik menggunakan Chart.js (CDN versi dipin 4.4.1): tren harga vs tahun, harga rata-rata per merek, jarak tempuh (km) vs harga, dan perbandingan harga asli vs prediksi. |
| **3. Pemanfaatan AI** | Chatbot FAQ jual-beli motor bekas (RAG mini dengan pencocokan kata kunci & kamus sinonim) dan tombol "Jelaskan Hasil" via Google Gemini REST API langsung dengan fallback otomatis. |
| **4. Aplikasi Jadi** | Web responsif berbasis Django dengan 5 halaman aktif (Beranda, Prediksi, Grafik, Chatbot, Riwayat), navigasi sidebar bergaya dashboard terang. |
| **(Tambahan) Firebase** | Penyimpanan riwayat hasil prediksi secara *server-side* ke Google Cloud Firestore (koleksi `prediksi_motor`). |

---

## 3. Sumber Data & Peringatan Jujur

- **Sumber Dataset:** Repositori GitHub `Mufti129/motor-price-id` (`dataset_mentah.csv`), memuat 17.000 baris data mentah.
- **PERINGATAN KEJUJURAN DATA:**  
  Berdasarkan analisis struktur dataset, data ini **kemungkinan besar dibuat oleh generator (sintetis), bukan data transaksi pasar nyata**. Indikasinya meliputi:
  1. Seluruh kolom `External_ID` memiliki pola awalan `gen_`.
  2. Distribusi sampel tiap merek berjumlah seragam persis 1.000 baris.
  3. Kolom URL berupa tautan query pencarian, serta deskripsi mengikuti format template seragam.
  
  Oleh karena itu, **angka hasil prediksi pada aplikasi ini merupakan model percontohan akademik Sistem Cerdas, bukan taksiran harga resmi dari pasar kendaraan motor**.

### Pembersihan Data (`ml/bersihkan_data.py`)
1. Membuang iklan bertanda `Is_DP_Clickbait == True` (harga merupakan uang muka/DP).
2. Membuang merek motor besar/premium (Harley-Davidson, BMW Motorrad, Royal Enfield, KTM) karena segmentasi pasar yang sangat berbeda dan jumlah sampel yang sedikit dapat merusak stabilitas estimasi regresi.
3. Membuang data duplikat dan anomali (km < 0, harga < Rp1.000.000).
4. Mengubah skala harga menjadi satuan juta Rupiah (dibagi 1.000.000).
5. Menghasilkan `data/motor_bekas.csv` bersih sebanyak **12.571 baris**.

---

## 4. Evaluasi & Keterbatasan Model Machine Learning

Data dibagi menjadi 80% data latih (10.056 baris) dan 20% data uji (2.515 baris) dengan `random_state=42`.

| Model Algoritma | MAE (Juta Rp) | RMSE (Juta Rp) | R² Uji | R² Latih | Status |
|---|---|---|---|---|---|
| **Random Forest (Terpilih)** | **4.93** | **13.59** | **0.872** | **0.986** | Model Aktif |
| **Regresi Linear (Pembanding)** | 9.06 | 16.59 | 0.810 | 0.796 | Pembanding |

### Keterbatasan Model:
1. **Overfitting pada Random Forest:** Skor $R^2$ latih mencapai 0.986 sementara $R^2$ uji sebesar 0.872. Selisih skor ini menunjukkan model cenderung menghafal pola data latih. Namun, Random Forest tetap dipilih karena menghasilkan kesalahan rata-rata ($MAE$) data uji paling kecil (Rp4,93 juta dibanding Rp9,06 juta).
2. **Multikolinearitas Kuat:** Fitur `tahun` dan `km` memiliki korelasi negatif yang sangat kuat (sekitar -0.95). Pada regresi linear, multikolinearitas ini dapat membuat koefisien bobot menjadi tidak stabil.

---

## 5. Struktur Direktori Proyek

```
Proyek/
├── manage.py                   # Skrip utilitas Django
├── config/                     # Konfigurasi utama Django (settings.py, urls.py)
├── ekspedisi/                  # Aplikasi utama
│   ├── views.py                # Kontroller logika tampilan dan endpoint API
│   ├── urls.py                 # Rute URL halaman dan AJAX
│   └── services/               # Lapisan layanan modular
│       ├── ml.py               # Pemuatan model, pipeline prediksi, agregat grafik
│       ├── ai.py               # Integrasi Google Gemini REST API & fallback
│       ├── faq.py              # Korpus 8 FAQ, pembersihan teks, sinonim RAG
│       └── firebase.py         # Klien Google Cloud Firestore Admin SDK
├── ml/
│   ├── bersihkan_data.py       # Pembersihan dataset mentah ke bersih
│   ├── latih_model.py          # Pelatihan dan evaluasi model regresi
│   ├── model_harga.joblib      # Bobot model pipeline terbaik tersimpan
│   └── metrik.json             # Metrik evaluasi dan metadata pilihan form
├── data/
│   ├── motor_bekas_mentah.csv  # Dataset mentah 17.000 baris
│   └── motor_bekas.csv         # Dataset bersih 12.571 baris
├── templates/                  # Template HTML Django
│   ├── base.html               # Kerangka utama dashboard indigo
│   ├── beranda.html            # Halaman ringkasan metrik & warning
│   ├── prediksi.html           # Formulir prediksi harga & AI explainer
│   ├── grafik.html             # Visualisasi 4 grafik Chart.js
│   ├── chatbot.html            # Antarmuka chatbot FAQ interaktif
│   └── riwayat.html            # Tabel riwayat Firestore
├── static/css/
│   └── style.css               # Desain dashboard terang bertema indigo
├── .env                        # Variabel rahasia lokal (DIABAIKAN GIT)
├── .env.example                # Contoh format variabel lingkungan
├── .gitignore                  # Berkas pengecualian Git
├── requirements.txt            # Daftar dependensi library Python
└── README.md                   # Dokumentasi lengkap proyek
```

---

## 6. Persyaratan Lingkungan & Instalasi

### Kebutuhan Sistem
- Windows 10/11
- Python 3.13 - 3.15
- Virtual Environment (`venv`)

### Langkah Menjalankan

1. **Buka Terminal / Command Prompt di folder proyek:**
   ```bash
   cd "d:\Mata Kuliah Semester 3\Muhammad Syaeful Fajar, S.Pd., M.Kom\Penugasan\Proyek"
   ```

2. **Aktifkan virtual environment:**
   ```powershell
   .\venv\Scripts\activate
   ```

3. **Pastikan konfigurasi lingkungan `.env` tersedia:**
   Buat atau periksa file `.env` di folder utama:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-1.5-flash
   FIREBASE_KEY_PATH=firebase-key.json
   ```
   *Catatan Keamanan: Jangan pernah mengunggah berkas `.env` atau `firebase-key.json` ke repositori publik.*

4. **Jalankan pembersihan data dan pelatihan model (jika belum dijalankan):**
   ```bash
   python ml/bersihkan_data.py
   python ml/latih_model.py
   ```

5. **Uji integritas aplikasi Django:**
   ```bash
   python manage.py check
   ```

6. **Jalankan server pengembangan Django:**
   ```bash
   python manage.py runserver
   ```

7. **Buka peramban (browser) di alamat:**
   `http://127.0.0.1:8000/`

---

## 7. Mekanisme Ketahanan Sistem (Fallback)

1. **Fallback AI (Gemini REST API):**
   Jika endpoint Gemini API gagal, API key belum diisi, kuota 429/503 habis, atau timeout (coba ulang maksimal 3 kali untuk error sementara):
   - Chatbot akan menyajikan jawaban langsung dari entri FAQ resmi dengan label `[AI sedang tidak tersedia]`.
   - Fitur "Jelaskan Hasil" pada prediksi akan menyajikan narasi otomatis berdasarkan faktor kilometer, tahun, dan pajak tanpa error.
2. **Fallback Database Firebase:**
   Jika file kunci `firebase-key.json` tidak ada, koneksi terputus, atau kuota habis:
   - Proses penaksiran harga tetap sukses menampilkan hasil.
   - Peringatan kecil ditampilkan bahwa riwayat belum tersimpan ke server cloud.
   - Halaman Riwayat menampilkan pesan ramah tanpa memicu *Internal Server Error (500)*.

---

## 8. Pembagian Tugas Kelompok (Template)

| Anggota Tim | NIM | Peran & Tanggung Jawab Utama | Kontribusi Kode |
|---|---|---|---|
| **Fauzy Ahmad Muzayyin** | 253307024 | Koordinator Proyek, Arsitektur Django, Integrasi Model ML, Firebase & Dokumentasi | `ekspedisi/`, `ml/`, `config/` |
| *(Dapat Diisi)* | *(NIM)* | Pengolahan Data & Feature Engineering | `ml/bersihkan_data.py`, `ml/metrik.json` |
| *(Dapat Diisi)* | *(NIM)* | Desain Antarmuka Dashboard (HTML & CSS) | `templates/`, `static/css/style.css` |
| *(Dapat Diisi)* | *(NIM)* | Pengujian Sistem & Integrasi RAG AI | `ekspedisi/services/faq.py`, `ai.py` |

---

## 9. Lisensi & Hak Cipta

Proyek ini disusun guna memenuhi evaluasi penugasan akademik Mata Kuliah Sistem Cerdas, Jurusan Teknik Elektro, Program Studi Teknik Informatika, Politeknik Negeri Madiun.
