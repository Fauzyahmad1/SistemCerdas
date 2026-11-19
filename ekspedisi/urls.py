# ekspedisi/urls.py
# Pemetaan rute URL untuk aplikasi web ekspedisi (prediksi harga motor bekas).

from django.urls import path
from ekspedisi import views

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("prediksi/", views.prediksi, name="prediksi"),
    path("grafik/", views.grafik, name="grafik"),
    path("chatbot/", views.chatbot, name="chatbot"),
    path("riwayat/", views.riwayat, name="riwayat"),
    
    # Endpoint API (AJAX)
    path("api/model-pilihan/", views.api_model_pilihan, name="api_model_pilihan"),
    path("api/jelaskan/", views.api_jelaskan_prediksi, name="api_jelaskan_prediksi"),
    path("api/jelaskan-grafik/", views.api_jelaskan_grafik, name="api_jelaskan_grafik"),
    path("api/chat/", views.api_chatbot, name="api_chatbot"),
]
