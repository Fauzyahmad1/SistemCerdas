# ekspedisi/views.py
# Modul views untuk menangani permintaan HTTP ke 5 halaman utama dan endpoint API.

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ekspedisi.services.ml import muat_metrik, prediksi_harga, ambil_data_grafik
from ekspedisi.services.ai import jawab_faq_ai, jelaskan_prediksi_ai, ambil_penjelasan_grafik
from ekspedisi.services.firebase import simpan_prediksi_firestore, ambil_riwayat_firestore


def beranda(request):
    """Halaman Beranda: ringkasan sistem, metrik evaluasi model, status modul, dan navigasi."""
    metrik = muat_metrik()
    hasil_model = metrik.get("hasil", {})
    
    # Ambil metrik untuk model terbaik
    model_terpilih = metrik.get("model_terpakai", "Random Forest")
    data_evaluasi = hasil_model.get(model_terpilih, {
        "mae": 4.93, "rmse": 13.59, "r2_uji": 0.872, "r2_latih": 0.986
    })
    
    # Ambil juga metrik pembanding (Linear Regression)
    eval_linear = hasil_model.get("Regresi Linear", {
        "mae": 9.06, "rmse": 16.59, "r2_uji": 0.81, "r2_latih": 0.796
    })

    konteks = {
        "halaman_aktif": "beranda",
        "metrik": metrik,
        "model_terpilih": model_terpilih,
        "data_evaluasi": data_evaluasi,
        "eval_linear": eval_linear,
    }
    return render(request, "beranda.html", konteks)


def prediksi(request):
    """
    Halaman Prediksi: Formulir penaksiran harga motor bekas,
    perhitungan model ML, penyimpanan riwayat ke Firestore, dan penjelasan AI.
    """
    metrik = muat_metrik()
    pilihan_model_dict = metrik.get("pilihan_model", {})
    daftar_merek = sorted(list(pilihan_model_dict.keys()))

    hasil_prediksi = None
    input_data = {}
    firebase_pesan = None
    firebase_sukses = False
    penjelasan_ai = None

    if request.method == "POST":
        merek = request.POST.get("merek", "").strip()
        model_motor = request.POST.get("model", "").strip()
        tahun = request.POST.get("tahun", "").strip()
        km = request.POST.get("km", "").strip()
        status_pajak = request.POST.get("status_pajak", "").strip()
        jenis_penjual = request.POST.get("jenis_penjual", "").strip()
        minta_penjelasan = request.POST.get("minta_penjelasan") == "1"

        input_data = {
            "merek": merek,
            "model": model_motor,
            "tahun": tahun,
            "km": km,
            "status_pajak": status_pajak,
            "jenis_penjual": jenis_penjual
        }

        try:
            # Hitung prediksi harga dengan pipeline ML
            harga = prediksi_harga(merek, model_motor, tahun, km, status_pajak, jenis_penjual)
            hasil_prediksi = harga

            # Simpan hasil ke Firebase Firestore (dibungkus try/except di service)
            firebase_sukses, firebase_pesan = simpan_prediksi_firestore(
                merek=merek,
                model_motor=model_motor,
                tahun=tahun,
                km=km,
                status_pajak=status_pajak,
                jenis_penjual=jenis_penjual,
                harga_prediksi=harga,
                model_ml=metrik.get("model_terpakai", "Random Forest")
            )

            # Jika opsi penjelasan dicentang saat submit form
            if minta_penjelasan:
                penjelasan_ai = jelaskan_prediksi_ai(
                    merek, model_motor, int(tahun), float(km), status_pajak, jenis_penjual, harga
                )

        except Exception as e:
            firebase_sukses = False
            firebase_pesan = f"Terjadi kesalahan saat memproses prediksi: {str(e)}"

    konteks = {
        "halaman_aktif": "prediksi",
        "daftar_merek": daftar_merek,
        "pilihan_model_json": json.dumps(pilihan_model_dict),
        "status_pajak_list": metrik.get("status_pajak", ["Hidup / Panjang", "Mati / Off", "Unknown"]),
        "jenis_penjual_list": metrik.get("jenis_penjual", ["Dealer", "Individual"]),
        "rentang_tahun": metrik.get("rentang_tahun", [2012, 2026]),
        "metrik": metrik,
        "hasil_prediksi": hasil_prediksi,
        "input_data": input_data,
        "firebase_sukses": firebase_sukses,
        "firebase_pesan": firebase_pesan,
        "penjelasan_ai": penjelasan_ai,
    }
    return render(request, "prediksi.html", konteks)


def grafik(request):
    """Halaman Grafik: menampilkan 4 grafik analitik motor bekas menggunakan Chart.js dan penjelasan AI."""
    data_grafik = ambil_data_grafik()
    penjelasan_grafik = ambil_penjelasan_grafik()
    konteks = {
        "halaman_aktif": "grafik",
        "data_grafik_json": json.dumps(data_grafik),
        "penjelasan_grafik": penjelasan_grafik,
    }
    return render(request, "grafik.html", konteks)


def chatbot(request):
    """Halaman Chatbot: Tanya jawab interaktif seputar tips dan regulasi jual beli motor bekas."""
    konteks = {
        "halaman_aktif": "chatbot",
    }
    return render(request, "chatbot.html", konteks)


def riwayat(request):
    """Halaman Riwayat: Menampilkan 20 data prediksi terakhir dari Firestore."""
    daftar_riwayat, status_koneksi, pesan_koneksi = ambil_riwayat_firestore(limit=20)
    konteks = {
        "halaman_aktif": "riwayat",
        "daftar_riwayat": daftar_riwayat,
        "status_koneksi": status_koneksi,
        "pesan_koneksi": pesan_koneksi,
    }
    return render(request, "riwayat.html", konteks)


# ======================== ENDPOINT API (AJAX) ========================

def api_model_pilihan(request):
    """Mengembalikan daftar model motor sesuai merek yang dipilih (JSON)."""
    merek = request.GET.get("merek", "")
    metrik = muat_metrik()
    daftar_model = metrik.get("pilihan_model", {}).get(merek, [])
    return JsonResponse({"model_list": daftar_model})


@csrf_exempt
def api_jelaskan_prediksi(request):
    """Endpoint untuk tombol 'Jelaskan Hasil' via AJAX."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "pesan": "Metode tidak diizinkan"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else request.POST
        merek = body.get("merek", "")
        model_motor = body.get("model", "")
        tahun = int(body.get("tahun", 2020))
        km = float(body.get("km", 10000))
        status_pajak = body.get("status_pajak", "Hidup / Panjang")
        jenis_penjual = body.get("jenis_penjual", "Individual")
        harga = float(body.get("harga", 0))

        penjelasan = jelaskan_prediksi_ai(merek, model_motor, tahun, km, status_pajak, jenis_penjual, harga)
        return JsonResponse({"status": "ok", "penjelasan": penjelasan})
    except Exception as e:
        return JsonResponse({"status": "error", "pesan": str(e)}, status=400)


@csrf_exempt
def api_chatbot(request):
    """Endpoint untuk pesan chat bot FAQ via AJAX."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "pesan": "Metode tidak diizinkan"}, status=405)

    try:
        if request.content_type == "application/json":
            body = json.loads(request.body.decode("utf-8"))
            pertanyaan = body.get("pertanyaan", "").strip()
        else:
            pertanyaan = request.POST.get("pertanyaan", "").strip()

        if not pertanyaan:
            return JsonResponse({"status": "error", "pesan": "Pertanyaan tidak boleh kosong"}, status=400)

        jawaban = jawab_faq_ai(pertanyaan)
        return JsonResponse({"status": "ok", "jawaban": jawaban})
    except Exception as e:
        return JsonResponse({"status": "error", "pesan": str(e)}, status=500)


@csrf_exempt
def api_jelaskan_grafik(request):
    """Endpoint AJAX untuk memperbarui analisis dan wawasan AI pada ke-4 grafik."""
    try:
        force = request.GET.get("force", "1") == "1" or request.POST.get("force", "1") == "1"
        penjelasan = ambil_penjelasan_grafik(force_refresh=force)
        return JsonResponse({"status": "ok", "penjelasan": penjelasan})
    except Exception as e:
        return JsonResponse({"status": "error", "pesan": str(e)}, status=500)
