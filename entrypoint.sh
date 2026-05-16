#!/bin/bash

# Вихід відразу, якщо будь де виникає помилка
set -e 

echo "Waiting for database..."
 until python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); s.connect(('$DB_HOST',
    int('${DB_PORT:-5432}')))" > /dev/null 2>&1; do
    echo "Database not ready yet - sleeping..."
    sleep 1
done
    
echo "Database started"

echo "Django configuration check..."
python manage.py check

echo "Running migrations..."
python manage.py migrate --noinput

echo "Create initial super user..."
python manage.py createsuperuser --no-input 2>/dev/null || echo "    Superuser already exists. Skipping."

echo "Seeds the database with initial test data..."
python manage.py seed_db

echo "Collect static files..."
python manage.py collectstatic

echo "Start server..."
python manage.py runserver 0.0.0.0:8000