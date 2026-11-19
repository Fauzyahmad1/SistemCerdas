# tes_firebase.py : mengecek apakah kunci Firebase dan Firestore sudah benar
import os
from dotenv import load_dotenv                       # membaca file .env
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()                                        # muat isi .env
kunci = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")
firebase_admin.initialize_app(credentials.Certificate(kunci))   # masuk dengan kunci server
db = firestore.client()                              # sambungan ke Firestore

ref = db.collection("tes_koneksi").document()        # satu dokumen percobaan
ref.set({"pesan": "halo", "waktu": firestore.SERVER_TIMESTAMP})
print("Tulis berhasil, id:", ref.id)
print("Baca:", ref.get().to_dict()["pesan"])
ref.delete()                                         # bersihkan lagi
print("Firebase siap dipakai.")