# Image Python
FROM python:3.12-slim

# Install dependensi sistem yang diperlukan
RUN apt-get update && \
    apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Atur nama work directory
WORKDIR /app-emokids

# Salin file requirements.txt ke container
COPY requirements.txt .

# Install dependensi aplikasi
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh isi direktori aplikasi ke container
COPY . .

# Expose port aplikasi
EXPOSE 5000

# Jalankan aplikasi
CMD ["gunicorn", "--workers", "6", "--bind", "0.0.0.0:5000", "--timeout", "3600",  "app:app"]

