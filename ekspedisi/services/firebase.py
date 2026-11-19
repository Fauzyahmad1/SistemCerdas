# ekspedisi/services/firebase.py
# Modul integrasi Firebase Firestore (Admin SDK) untuk menyimpan dan membaca riwayat prediksi.

import os
from pathlib import Path
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

_firestore_client = None


def get_firestore_client():
    """
    Mengambil atau menginisialisasi klien Firestore Admin.
    Kunci akun layanan dibaca dari variabel lingkungan FIREBASE_KEY_PATH.
    Jika terjadi kesalahan (kunci tidak ada, offline, dll), kembalikan None tanpa crash.
    """
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    try:
        path_kunci = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json").strip()
        if not path_kunci:
            return None

        # Resolve path relatif terhadap folder root proyek jika perlu
        p = Path(path_kunci)
        if not p.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent.parent
            p = base_dir / path_kunci

        if not p.exists():
            return None

        # Inisialisasi firebase_admin hanya jika belum diinisialisasi
        if not firebase_admin._apps:
            sertifikat = credentials.Certificate(str(p))
            firebase_admin.initialize_app(sertifikat)

        _firestore_client = firestore.client()
        return _firestore_client
    except Exception:
        # Fallback aman jika inisialisasi gagal
        return None


def simpan_prediksi_firestore(merek, model_motor, tahun, km, status_pajak, jenis_penjual, harga_prediksi, model_ml="Random Forest"):
    """
    Menyimpan satu entri hasil prediksi motor ke koleksi Firestore 'prediksi_motor'.
    Mengembalikan tuple (sukses: bool, pesan: str).
    """
    try:
        db = get_firestore_client()
        if db is None:
            return False, "Koneksi Firebase Firestore tidak tersedia atau kunci belum valid."

        data_dokumen = {
            "merek": str(merek),
            "model": str(model_motor),
            "tahun": int(tahun),
            "km": float(km),
            "status_pajak": str(status_pajak),
            "jenis_penjual": str(jenis_penjual),
            "harga_prediksi": float(harga_prediksi),
            "model_ml": str(model_ml),
            "dibuat_pada": firestore.SERVER_TIMESTAMP
        }

        db.collection("prediksi_motor").add(data_dokumen)
        return True, "Data berhasil disimpan ke riwayat Firestore."
    except Exception as e:
        return False, f"Penyimpanan riwayat ke Firebase gagal: {str(e)}"


def ambil_riwayat_firestore(limit=20):
    """
    Mengambil data riwayat prediksi terbaru dari koleksi 'prediksi_motor' (maksimal 20 data).
    Mengembalikan tuple (daftar_riwayat: list, status_koneksi: bool, pesan: str).
    """
    try:
        db = get_firestore_client()
        if db is None:
            return [], False, "Layanan Firebase Firestore tidak terhubung. Periksa konfigurasi kunci atau koneksi internet."

        koleksi = db.collection("prediksi_motor")
        # Urutkan berdasarkan waktu pembuatan terbaru
        dokumen_stream = koleksi.order_by("dibuat_pada", direction=firestore.Query.DESCENDING).limit(limit).stream()

        daftar = []
        for doc in dokumen_stream:
            item = doc.to_dict()
            item["id"] = doc.id
            waktu = item.get("dibuat_pada")
            if waktu and hasattr(waktu, "strftime"):
                item["waktu_tampil"] = waktu.strftime("%d %b %Y, %H:%M WIB")
            elif waktu:
                item["waktu_tampil"] = str(waktu)
            else:
                item["waktu_tampil"] = "Baru saja"
            daftar.append(item)

        return daftar, True, "Berhasil memuat data riwayat dari Firestore."
    except Exception as e:
        return [], False, f"Terjadi kendala saat membaca data Firestore: {str(e)}"
