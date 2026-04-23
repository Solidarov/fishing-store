#!/bin/bash

# Вихід відразу, якщо будь де виникає помилка
set -e 

# echo "Waiting for database..."
# while ! nc -z $DB_HOST $DB_PORT; do
#   sleep 0.1
# done
# echo "Database started"

echo "Перевірка конфігурації Django..."
python manage.py check

echo "Запис міграцій до бази даних..."
python manage.py migrate --noinput

echo "Запуск серверу..."
python manage.py runserver 0.0.0.0:8000