import os

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.static import serve

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

urlpatterns = [
    path('', include('ads.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login_social.html')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    re_path(
        r'^favicon\.ico$',
        serve,
        {
            'path': 'favicon.ico',
            'document_root': os.path.join(BASE_DIR, 'static'),
        },
    ),
]
