#!/bin/bash

#check if python3 is installed
if ! [ -x "$(command -v python3)" ]; then
  echo 'Error: python3 is not installed.' >&2
  exit 1
fi

#check if pip3 is installed
if ! [ -x "$(command -v pip3)" ]; then
  echo 'Error: pip3 is not installed.' >&2
  exit 1
fi

#pick a supported python (Django 6.1 needs Python 3.12+; 3.15 is what the pins are tested on)
PY=""
for candidate in python3.15 python3.14 python3.13 python3.12; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then
  echo 'Error: Python 3.12 or newer is required.' >&2
  exit 1
fi

#create virtual environment
"$PY" -m venv venv

#activate virtual environment
source venv/bin/activate

#install requirements
pip install -r requirements.txt

#create .env file in PrivatePing/settings with a freshly generated secret key
ENV_FILE=PrivatePing/settings/.env
if [ ! -f "$ENV_FILE" ]; then
  SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
  ADMIN=$(python -c 'import secrets; print(secrets.token_urlsafe(12))')
  {
    echo "SECRET_KEY='$SECRET'"
    echo "SECRET_ADMIN_URL='$ADMIN/'"
  } > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Admin panel: http://localhost:8000/$ADMIN/admin/"
fi

#run migrations
python manage.py migrate

#run server
python manage.py runserver
