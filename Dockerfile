FROM python:3.11-slim

WORKDIR /app

# Hindari pembuatan file .pyc dan aktifkan log langsung
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependensi sistem jika diperlukan
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Siapkan user non-root (standar Hugging Face user UID 1000)
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Copy semua file proyek
COPY --chown=user:user . /app

# Kumpulkan file statis
RUN python manage.py collectstatic --no-input

# Hugging Face Spaces membaca port 7860
EXPOSE 7860

# Jalankan migrasi dan nyalakan web dengan Gunicorn pada port 7860
CMD ["sh", "-c", "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:7860 --workers 2 --timeout 120"]
