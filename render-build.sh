#!/bin/bash
# Render build script - executed after repository clone and before server start

set -e

echo "=========================================="
echo "Bibel Backend - Render Build Script"
echo "=========================================="

echo "1. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "2. Running database migrations..."
python manage.py migrate

echo "3. Creating default admin user..."
python manage.py create_default_admin

echo "4. Collecting static files..."
python manage.py collectstatic --noinput

echo "=========================================="
echo "✓ Build completed successfully!"
echo "=========================================="
