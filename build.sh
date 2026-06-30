#!/bin/bash
echo "Building Project..."
python3 -m pip install -r requirements.txt
echo "Running collectstatic..."
python3 manage.py collectstatic --noinput --clear
echo "Running migrations..."
python3 manage.py migrate
