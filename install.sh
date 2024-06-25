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

#install virtualenv
pip3 install virtualenv

#create virtual environment
python3 -m venv venv

#activate virtual environment
source venv/bin/activate

#install requirements
pip3 install -r requirements.txt

#create .env file in PrivatePing/settings
echo "SECRET_KEY='*$j@tpltfyblml&*1d+n9t@il^0xef4=bvdu&!7r=zvoq$a19g'" > PrivatePing/settings/.env
echo "SECRET_ADMIN_URL=''" >> PrivatePing/settings/.env
echo "HCAPTCHA_SITEKEY='10000000-ffff-ffff-ffff-000000000001'" >> PrivatePing/settings/.env
echo "HCAPTCHA_SECRET='0x0000000000000000000000000000000000000000'" >> PrivatePing/settings/.env
#run migrations
python3 manage.py migrate

#run server
python3 manage.py runserver
