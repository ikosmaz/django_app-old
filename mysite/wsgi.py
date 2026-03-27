"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

os.environ["PYTHONIOENCODING"] = "UTF-8" #Added to get emoji
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

os.environ['DJANGO_EMAIL_BACKEND'] = 'django.core.mail.backends.smtp.EmailBackend'
os.environ['DJANGO_EMAIL_HOST'] = 'smtp.gmail.com'
os.environ['DJANGO_EMAIL_PORT'] = '587'
os.environ['DJANGO_EMAIL_USE_TLS'] = '1'
os.environ['DJANGO_EMAIL_HOST_USER'] = 'kosmazisa@gmail.com'
os.environ['DJANGO_EMAIL_HOST_PASSWORD'] = 'fdhj wzjo afrp dskp'
os.environ['DJANGO_DEFAULT_FROM_EMAIL'] = 'kosmazisa@gmail.com'


application = get_wsgi_application()
