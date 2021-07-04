from django.urls import path

from rest_framework import routers
from .api import VideoViewSet, SeasonViewSet, VideoList, ImageModelViewSet
from .views import get_info

router = routers.DefaultRouter()
router.register("api/videos", VideoViewSet, "videos")
router.register("api/seasons", SeasonViewSet, "seasons")
router.register("api/images", ImageModelViewSet, "images")

urlpatterns = [
    path("api/video_type/", VideoList.as_view()),
    path("api/info/", get_info),
]

urlpatterns += router.urls
