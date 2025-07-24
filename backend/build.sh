#!/bin/bash

# implement build file for render

# Exit on error
set -e

echo "Starting build process..."

# Install Python dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run Django migrations
echo "Running database migrations..."
python manage.py makemigrations users academic community messaging content
python manage.py migrate --noinput

python manage.py populate_db

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"