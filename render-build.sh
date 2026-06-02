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
echo "   (admin user admin@example.com will be created if missing)"
python manage.py migrate

echo "3. Creating default admin user via script..."
python scripts/create_admin_user.py --username admin --email admin@example.com --password StrongPass123!

echo "4. Collecting static files..."
python manage.py collectstatic --noinput

echo "=========================================="
echo "✓ Build completed successfully!"
echo "=========================================="
