from django.urls import path

from rest_framework import routers
from .api import VideoViewSet, ImageModelViewSet, GroupViewSet
from .views import get_info

router = routers.DefaultRouter()
router.register("api/videos", VideoViewSet, "videos")
router.register("api/images", ImageModelViewSet, "images")
router.register("api/groups", GroupViewSet, "groups")

urlpatterns = [
    path("api/info/", get_info),
]

urlpatterns += router.urls
