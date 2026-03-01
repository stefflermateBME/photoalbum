FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Create dirs (OpenShift random UID is ok if mounted volume provides perms)dd
RUN mkdir -p /data/media /app/staticfiles

ENV DJANGO_MEDIA_ROOT=/data/media
ENV DJANGO_STATIC_ROOT=/app/staticfiles

EXPOSE 8080

# Start: migrate then collectstatic then gunicorn
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 60"]