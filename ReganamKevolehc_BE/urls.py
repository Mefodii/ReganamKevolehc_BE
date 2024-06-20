"""ReganamKevolehc_BE URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from ReganamKevolehc_BE.views import get_consts

urlpatterns = [
    path('admin/', admin.site.urls),
    path('watching/', include("watching.urls")),
    path('listening/', include("listening.urls")),
    path('contenting/', include("contenting.urls")),
    path("api/sync_check/", get_consts),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.CONTENTING_TEMP_MEDIA_URL, document_root=settings.CONTENTING_TEMP_MEDIA_ROOT)
urlpatterns += static(settings.CONTENTING_VIDEO_MEDIA_URL, document_root=settings.CONTENTING_VIDEO_MEDIA_ROOT)
urlpatterns += static(settings.CONTENTING_AUDIO_MEDIA_URL, document_root=settings.CONTENTING_AUDIO_MEDIA_ROOT)
urlpatterns += static(settings.PLAYLIST_MEDIA_URL, document_root=settings.PLAYLIST_MEDIA_ROOT)
