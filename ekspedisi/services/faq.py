# ekspedisi/services/faq.py
# Modul pencarian FAQ berbasis RAG mini (pembersihan teks, sinonim, pencarian kata kunci).

import re

# 8 Entri FAQ resmi jual-beli motor bekas
DATA_FAQ = [
    {
        "id": 1,
        "kategori": "surat",
        "pertanyaan": "Bagaimana cara mengecek keaslian dan kelengkapan surat STNK dan BPKB motor bekas?",
        "kata_kunci": ["stnk", "bpkb", "surat", "asli", "palsu", "dokumen", "nomor", "rangka", "mesin", "legalitas"],
        "jawaban": "Cocokkan nomor rangka dan nomor mesin fisik di motor dengan yang tercetak di STNK dan BPKB. Periksa hologram BPKB di bawah cahaya dan pastikan tidak ada bekas coretan atau hapusan mencurigakan."
    },
    {
        "id": 2,
        "kategori": "pajak",
        "pertanyaan": "Bagaimana cara memeriksa status pajak motor dan konsekuensi jika pajak mati?",
        "kata_kunci": ["pajak", "mati", "hidup", "telat", "denda", "pkb", "samsat", "stnk", "tahunan", "kaleng", "plat"],
        "jawaban": "Cek tanggal jatuh tempo Pajak Kendaraan Bermotor (PKB) dan masa berlaku plat 5 tahunan pada lembar STNK atau aplikasi Samsat online. Jika pajak mati, perhitungkan biaya tunggakan dan denda sebagai bahan negosiasi potongan harga."
    },
    {
        "id": 3,
        "kategori": "balik_nama",
        "pertanyaan": "Bagaimana prosedur dan persyaratan untuk melakukan balik nama motor bekas?",
        "kata_kunci": ["balik", "nama", "bbn", "mutasi", "prosedur", "syarat", "samsat", "ktp", "pemilik"],
        "jawaban": "Siapkan BPKB asli, STNK asli, fotokopi KTP pemilik baru, serta kwitansi jual-beli bermeterai yang ditandatangani penjual. Datangi kantor Samsat terdekat untuk melakukan cek fisik kendaraan sebelum proses administrasi balik nama."
    },
    {
        "id": 4,
        "kategori": "mesin",
        "pertanyaan": "Bagaimana cara memeriksa kondisi mesin motor bekas agar tidak tertipu?",
        "kata_kunci": ["mesin", "kondisi", "bunyi", "oli", "suara", "knalpot", "asap", "bocor", "rembes", "halus", "kasar"],
        "jawaban": "Dengarkan suara mesin saat stasioner (langsam), pastikan bunyinya halus tanpa ketukan logam yang kasar. Periksa apakah ada rembesan oli di sela blok mesin dan pastikan knalpot tidak mengeluarkan asap putih pekat."
    },
    {
        "id": 5,
        "kategori": "harga",
        "pertanyaan": "Faktor apa saja yang paling mempengaruhi penurunan harga motor bekas?",
        "kata_kunci": ["faktor", "turun", "penurun", "harga", "depresiasi", "jatuh", "kilometer", "odometer", "tahun", "lecet", "jatuh"],
        "jawaban": "Faktor utama penurun harga adalah usia kendaraan (tahun pembuatan), tingginya jarak tempuh (kilometer), status pajak mati, riwayat kecelakaan berat, serta bodi dan mesin yang butuh perbaikan besar."
    },
    {
        "id": 6,
        "kategori": "tawar",
        "pertanyaan": "Apa saja tips tawar-menawar harga motor bekas agar mendapatkan harga wajar?",
        "kata_kunci": ["tips", "tawar", "menawar", "nego", "negosiasi", "terbaik", "murah", "trik", "diskon"],
        "jawaban": "Riset harga pasaran model sejenis sebelum bertemu penjual, lalu manfaatkan minus fisik seperti ban aus, pajak telat, atau lecet bodi sebagai alasan masuk akal untuk menawar harga lebih rendah."
    },
    {
        "id": 7,
        "kategori": "uji_jalan",
        "pertanyaan": "Bagaimana cara melakukan uji jalan (test drive) motor bekas yang benar?",
        "kata_kunci": ["uji", "jalan", "test", "drive", "stang", "rem", "suspensi", "tarikan", "kopling", "getar", "shock"],
        "jawaban": "Uji kelembutan tarikan gas, kepakeman rem depan-belakang, kestabilan stang kemudi pada jalan lurus, dan redaman shockbreaker saat melintasi jalan bergelombang atau polisi tidur."
    },
    {
        "id": 8,
        "kategori": "dokumen",
        "pertanyaan": "Dokumen apa saja yang harus disiapkan penjual dan pembeli saat transaksi jual beli?",
        "kata_kunci": ["dokumen", "disiapkan", "transaksi", "kwitansi", "meterai", "kelengkapan", "jual", "beli", "faktur"],
        "jawaban": "Penjual wajib menyerahkan STNK asli, BPKB asli, faktur pembelian jika ada, serta kwitansi bermeterai bertandatangan sesuai KTP. Pembeli perlu menyiapkan identitas diri asli (KTP) dan bukti pelunasan."
    }
]

# Kamus sinonim untuk menyamakan istilah umum dari pengguna
SINONIM = {
    "odometer": "kilometer",
    "jarak": "kilometer",
    "km": "kilometer",
    "surat": "stnk",
    "dokumen": "stnk",
    "bpkb": "stnk",
    "pajek": "pajak",
    "pkb": "pajak",
    "bbn": "balik",
    "mutasi": "balik",
    "bunyi": "suara",
    "rusak": "kondisi",
    "rembes": "oli",
    "nego": "tawar",
    "menawar": "tawar",
    "negosiasi": "tawar",
    "diskon": "tawar",
    "nyoba": "uji",
    "test": "uji",
    "testdrive": "uji",
    "shock": "suspensi",
    "shockbreaker": "suspensi",
    "kuitansi": "kwitansi",
    "meterai": "kwitansi",
    "depresiasi": "turun",
}


def bersihkan_teks(teks):
    """Mengubah ke huruf kecil, menghapus tanda baca, dan memecah menjadi daftar kata."""
    teks = teks.lower()
    teks = re.sub(r"[^a-z0-9\s]", " ", teks)
    kata_list = [k.strip() for k in teks.split() if len(k.strip()) > 1]
    return kata_list


def cari_faq(query_teks):
    """
    Mencari 2 entri FAQ paling relevan dengan mencocokkan kata kunci dan sinonim.
    Jika tidak ada kata yang cocok sama sekali, kembalikan ([], False).
    """
    kata_query = bersihkan_teks(query_teks)
    if not kata_query:
        return [], False

    # Tambahkan sinonim jika ditemukan kata yang cocok
    kata_diperluas = set(kata_query)
    for kata in kata_query:
        if kata in SINONIM:
            kata_diperluas.add(SINONIM[kata])

    skor_faq = []
    for faq in DATA_FAQ:
        # Kumpulan kata target dari kata kunci, pertanyaan, dan jawaban
        teks_faq = f"{faq['pertanyaan']} {faq['jawaban']}"
        kata_target = set(faq["kata_kunci"] + bersihkan_teks(teks_faq))

        # Hitung irisan kata
        cocok = kata_diperluas.intersection(kata_target)
        skor = len(cocok)

        # Bobot lebih tinggi jika kata kunci utama cocok
        for k in faq["kata_kunci"]:
            if k in kata_diperluas:
                skor += 2

        if skor > 0:
            skor_faq.append((skor, faq))

    # Urutkan berdasarkan skor tertinggi
    skor_faq.sort(key=lambda x: x[0], reverse=True)

    if not skor_faq:
        return [], False

    # Ambil maksimal 2 entri teratas
    faq_terpilih = [item[1] for item in skor_faq[:2]]
    return faq_terpilih, True
