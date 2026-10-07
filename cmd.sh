# venv start.
.\venv\Scripts\Activate.ps1    

python -m venv venv && source venv/bin/activate
pip install django pillow
django-admin startproject config .
python manage.py startapp shop
mkdir -p templates/registration


pip install djangorestframework djangorestframework-simplejwt stripe django-cors-headers

pip install django-environ


# database migration
python manage.py makemigrations shop
python manage.py migrate


pip install drf-spectacular


python manage.py test shop -v 2

