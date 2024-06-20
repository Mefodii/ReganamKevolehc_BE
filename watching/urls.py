from rest_framework import routers

from .api import VideoViewSet, ImageModelViewSet, GroupViewSet

router = routers.DefaultRouter()
router.register("api/videos", VideoViewSet, "videos")
router.register("api/images", ImageModelViewSet, "images")
router.register("api/groups", GroupViewSet, "groups")

urlpatterns = router.urls
