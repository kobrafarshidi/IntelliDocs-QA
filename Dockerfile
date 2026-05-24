FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/chroma /app/media

EXPOSE 8000

CMD ["sh", "-c", "python manage.py makemigrations documents qa --noinput && python manage.py migrate --noinput && python manage.py collectstatic --noinput && (python manage.py createsuperuser --noinput --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL || true) && gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 2 --timeout 120"]
