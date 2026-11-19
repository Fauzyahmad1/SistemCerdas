# ekspedisi/services/ai.py
# Modul integrasi AI: memanggil Google Gemini REST API langsung memakai library requests.

import os
import time
import requests
from dotenv import load_dotenv
from ekspedisi.services.faq import cari_faq

# Muat variabel lingkungan dari .env secara aman
load_dotenv()


def tanya_llm(prompt):
    """
    Mengirim prompt langsung ke Google Gemini REST API via HTTP POST JSON.
    - Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent
    - Header: x-goog-api-key: {GEMINI_API_KEY}
    - Body: {"contents": [{"parts": [{"text": prompt}]}]}
    - Ekstraksi jawaban: respon["candidates"][0]["content"]["parts"][0]["text"]
    - Timeout: 30 detik.
    - Coba ulang maksimal 3 kali (jeda 2, 4, 6 detik) HANYA untuk error sementara (503 atau 429).
    - Untuk error 400, 401, 403: langsung berhenti tanpa mencoba ulang.
    - Mengembalikan teks jawaban atau None jika gagal / key kosong.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_env = os.getenv("GEMINI_MODEL", "").strip()

    # Jika API key belum dikonfigurasi, langsung return None untuk memicu fallback
    if not api_key:
        return None

    # Tentukan model utama dari .env
    if not model_env or " " in model_env:
        model_utama = "gemini-flash-lite-latest"
    else:
        model_utama = model_env.replace("models/", "").strip()

    # Siapkan daftar model prioritas (jika model utama sedang overload/timeout di server Google, coba flash-lite)
    model_kandidat = [model_utama]
    if model_utama != "gemini-flash-lite-latest":
        model_kandidat.append("gemini-flash-lite-latest")

    jedas = [2, 4, 6]

    for model in model_kandidat:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        for percobaan in range(3):
            try:
                respons = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                # Jika berhasil (HTTP 200)
                if respons.status_code == 200:
                    data = respons.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                    return None

                # Error autentikasi atau client (400, 401, 403): jangan diulang
                if respons.status_code in [400, 401, 403]:
                    return None

                # Jika model 404 (tidak tersedia/deprecated), langsung ganti ke kandidat berikutnya
                if respons.status_code == 404:
                    break

                # Error selain 429 dan 503 tidak perlu diulang
                if respons.status_code not in [429, 503]:
                    break

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                # Error timeout atau koneksi ke model ini, coba sekali lagi atau lanjut ke kandidat model cadangan
                if percobaan == 0 and len(model_kandidat) > 1 and model != "gemini-flash-lite-latest":
                    break
            except Exception:
                return None

            # Beri jeda sebelum mencoba ulang hanya untuk error sementara (503 / 429)
            if percobaan < 2:
                time.sleep(jedas[percobaan])

    return None


def jawab_faq_ai(pertanyaan):
    """
    Menjawab pertanyaan seputar jual-beli motor bekas:
    1. Mencari 2 FAQ paling relevan (RAG mini).
    2. Jika tidak ada yang relevan, jawab default tanpa memanggil LLM.
    3. Jika ada, susun prompt dan tanyakan ke Google Gemini REST API.
    4. Jika Gemini gagal atau key kosong, gunakan fallback FAQ dengan label (AI sedang tidak tersedia).
    """
    faq_terpilih, ada_faq = cari_faq(pertanyaan)

    # Jika tidak ada topik FAQ yang relevan
    if not ada_faq or not faq_terpilih:
        return (
            "Maaf, informasi itu belum ada di FAQ resmi. "
            "Silakan hubungi penjual untuk rincian lebih lanjut."
        )

    # Susun konteks dari maksimal 2 entri FAQ
    konteks_faq = ""
    for idx, f in enumerate(faq_terpilih, start=1):
        konteks_faq += f"FAQ {idx}: {f['pertanyaan']}\nJawaban: {f['jawaban']}\n\n"

    # Pola prompt terstruktur: Peran + Konteks + Batasan + Format
    prompt = (
        "Peran: Anda adalah asisten virtual layanan pelanggan jual-beli motor bekas yang ramah dan solutif.\n"
        f"Konteks FAQ Resmi:\n{konteks_faq}\n"
        f"Pertanyaan Pengguna: {pertanyaan}\n\n"
        "Batasan: Jawab maksimal 2 kalimat HANYA berdasarkan konteks FAQ resmi di atas. "
        "Dilarang mengarang informasi baru di luar teks FAQ. Jika konteks tidak relevan, nyatakan belum tersedia.\n"
        "Format: Jawaban langsung, singkat dan jelas dalam Bahasa Indonesia (maksimal 2 kalimat)."
    )

    jawaban_llm = tanya_llm(prompt)
    if jawaban_llm:
        return jawaban_llm

    # Fallback jika koneksi Gemini API gagal atau key belum diisi
    faq_utama = faq_terpilih[0]
    return (
        f"(AI sedang tidak tersedia)\n\n"
        f"Berdasarkan FAQ resmi kami:\n{faq_utama['jawaban']}"
    )


def jelaskan_prediksi_ai(merek, model_motor, tahun, km, status_pajak, jenis_penjual, harga_prediksi):
    """
    Meminta penjelasan atas hasil taksiran harga motor bekas:
    - Mengirim parameter motor dan harga ke Gemini REST API.
    - AI dilarang mengarang angka di luar harga_prediksi.
    - Jika Gemini gagal atau key kosong, gunakan fallback narasi otomatis dari angka.
    """
    # Pola prompt: Peran + Konteks + Batasan + Format
    prompt = (
        "Peran: Anda adalah analis penilai harga kendaraan motor bekas profesional di Indonesia.\n"
        f"Konteks Motor:\n"
        f"- Merek: {merek}\n"
        f"- Model: {model_motor}\n"
        f"- Tahun Pembuatan: {tahun}\n"
        f"- Jarak Tempuh: {km:,.0f} km\n"
        f"- Status Pajak: {status_pajak}\n"
        f"- Penjual: {jenis_penjual}\n"
        f"- Hasil Prediksi Model Machine Learning: Rp{harga_prediksi:.2f} Juta\n\n"
        f"Batasan: Jelaskan secara singkat dan logis mengapa motor ini dihargai sekitar Rp{harga_prediksi:.2f} Juta "
        f"berdasarkan kombinasi usia, kilometer, dan status pajaknya. Panjang 2 hingga 3 kalimat saja. "
        f"DILARANG mengarang angka taksiran lain di luar Rp{harga_prediksi:.2f} Juta.\n"
        "Format: Paragraf singkat yang mudah dimengerti."
    )

    jawaban_llm = tanya_llm(prompt)
    if jawaban_llm:
        return jawaban_llm

    # Fallback teks otomatis jika Gemini REST API tidak terhubung
    kondisi_pajak = "masih hidup dan tertib" if "hidup" in status_pajak.lower() else "perlu pembaruan atau pelunasan tunggakan"
    return (
        f"Taksiran harga sekitar Rp{harga_prediksi:.2f} Juta untuk {merek} {model_motor} ({tahun}) "
        f"dihitung secara objektif dengan jarak tempuh {km:,.0f} km dan status pajak yang {kondisi_pajak}. "
        f"Penjualan melalui {jenis_penjual} ini mencerminkan depresiasi wajar berdasarkan usia dan pola pemakaian kendaraan."
    )


# ==================== PENJELASAN AI UNTUK GRAFIK ====================

# Cache dalam memori agar tidak memanggil API berulang-ulang pada setiap reload halaman
_cache_penjelasan_grafik = None

# Penjelasan baku (fallback) berbasis statistik nyata dataset motor bekas
PENJELASAN_GRAFIK_DEFAULT = {
    "tahun": (
        "Grafik menunjukkan korelasi positif yang kuat antara tahun pembuatan dan nilai jual motor. "
        "Depresiasi kendaraan terlihat jelas di mana unit tua (2013-2015) berada di kisaran Rp5-8 Juta, "
        "sedangkan unit muda (2024-2026) mempertahankan nilai tinggi hingga Rp33-38 Juta karena kondisi mesin prima dan teknologi mutakhir."
    ),
    "merek": (
        "Merek skuter gaya hidup Eropa (Piaggio Rp70,3 Jt & Vespa Rp47,6 Jt) serta motor sport (Kawasaki Rp48,9 Jt) mendominasi segmen harga tertinggi. "
        "Sementara itu, merek komuter harian massal seperti Yamaha (Rp23,8 Jt) dan Honda (Rp17,3 Jt) memiliki harga pasar yang jauh lebih terjangkau, likuid, dan stabil."
    ),
    "km": (
        "Terdapat tren penurunan harga yang konsisten seiring bertambahnya angka odometer (jarak tempuh kendaraan). "
        "Motor dengan kilometer rendah (<10.000 km) memiliki nilai tertinggi rata-rata Rp36,9 Jt karena keausan komponen mekanikal masih minim dan risiko biaya perbaikan kecil."
    ),
    "prediksi_vs_asli": (
        "Sebagian besar batang prediksi Random Forest berimpit presisi dengan harga aktual pada sampel uji (skor R2 uji 0.872 dan MAE Rp4.93 Juta). "
        "Hal ini membuktikan model Machine Learning berhasil menangkap pola interaksi fitur tahun, merek, jarak tempuh, dan status pajak dengan keandalan tinggi."
    ),
    "sumber": "Analisis Cerdas Data"
}


def ambil_penjelasan_grafik(force_refresh=False):
    """
    Mengambil wawasan analitik cerdas untuk ke-4 grafik visualisasi:
    1. Tren Harga Rata-Rata vs Tahun
    2. Harga Rata-Rata per Merek
    3. Hubungan Jarak Tempuh (KM) vs Harga
    4. Perbandingan Harga Asli vs Prediksi Model

    - Pada pemuatan awal (force_refresh=False): langsung mengembalikan cache atau
      penjelasan berbasis data nyata (0ms latency, anti-lag).
    - Jika force_refresh=True (misal tombol segarkan atau panggilan latar belakang):
      memanggil Google Gemini REST API dan memperbarui cache.
    """
    global _cache_penjelasan_grafik

    # Jika pemanggilan awal biasa dan cache belum ada, isi dengan penjelasan default agar halaman terbuka instan
    if not force_refresh:
        if _cache_penjelasan_grafik is not None:
            return _cache_penjelasan_grafik
        _cache_penjelasan_grafik = PENJELASAN_GRAFIK_DEFAULT.copy()
        return _cache_penjelasan_grafik

    prompt = (
        "Peran: Anda adalah analis data otomotif senior yang menginterpretasikan visualisasi data pasar motor bekas di Indonesia.\n\n"
        "Konteks Data Nyata:\n"
        "1. Tren Harga vs Tahun (2012-2026): Unit tua 2013-2014 rata-rata Rp5-6 Jt, lalu naik konsisten mencapai Rp31 Jt di 2021 dan puncak Rp38 Jt di 2026.\n"
        "2. Harga per Merek: Piaggio (Rp70 Jt), Kawasaki (Rp49 Jt), Vespa (Rp48 Jt) memimpin harga tertinggi. Merek komuter massal Yamaha (Rp24 Jt) dan Honda (Rp17 Jt) lebih ekonomis. Motor listrik di kisaran Rp19-28 Jt.\n"
        "3. Jarak Tempuh (KM) vs Harga: KM 0-10rb (Rp37 Jt), 10-20rb (Rp29 Jt), 20-35rb (Rp23 Jt), turun hingga >100rb ke Rp11 Jt.\n"
        "4. Prediksi vs Asli: Model Random Forest memiliki skor R2 Uji 0.872 dan MAE Rp4.93 Jt, prediksi berimpit presisi dengan harga aktual.\n\n"
        "Tugas: Tuliskan penjelasan wawasan analitik yang ringkas dan tajam untuk MASING-MASING dari 4 grafik di atas.\n"
        "Batasan:\n"
        "- Bahasa Indonesia profesional dan lugas.\n"
        "- Untuk setiap grafik, tulis tepat 2 kalimat padat yang menjelaskan tren data serta makna ekonominya.\n"
        "- Format jawaban WAJIB berupa JSON valid dengan kunci: 'tahun', 'merek', 'km', 'prediksi_vs_asli'.\n"
        "Contoh format:\n"
        "{\"tahun\": \"...\", \"merek\": \"...\", \"km\": \"...\", \"prediksi_vs_asli\": \"...\"}"
    )

    try:
        raw_res = tanya_llm(prompt)
        if raw_res:
            import json as json_mod
            teks_json = raw_res.strip()
            # Bersihkan blok markdown ```json jika ada
            if "```" in teks_json:
                baris_list = teks_json.split("\n")
                baris_bersih = [b for b in baris_list if not b.strip().startswith("```")]
                teks_json = "\n".join(baris_bersih).strip()

            awal = teks_json.find("{")
            akhir = teks_json.rfind("}")
            if awal != -1 and akhir != -1:
                teks_json = teks_json[awal:akhir + 1]
                data_dict = json_mod.loads(teks_json)
                kunci_wajib = ["tahun", "merek", "km", "prediksi_vs_asli"]
                if all(k in data_dict and isinstance(data_dict[k], str) and data_dict[k].strip() for k in kunci_wajib):
                    data_dict["sumber"] = "Gemini AI"
                    _cache_penjelasan_grafik = data_dict
                    return data_dict
    except Exception:
        pass

    fallback = PENJELASAN_GRAFIK_DEFAULT.copy()
    _cache_penjelasan_grafik = fallback
    return fallback
