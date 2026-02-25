FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_STATIC_ROOT=/data/static
ENV DJANGO_MEDIA_ROOT=/data/media

RUN python manage.py collectstatic --noinput || true

EXPOSE 8080
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080"]