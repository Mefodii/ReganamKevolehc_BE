from django.urls import path

from rest_framework import routers
from .api import ArtistViewSet, ReleaseViewSet, TrackViewSet
from .views import get_info

router = routers.DefaultRouter()
router.register("api/artists", ArtistViewSet, "artists")
router.register("api/releases", ReleaseViewSet, "releases")
router.register("api/tracks", TrackViewSet, "tracks")

urlpatterns = [
    path("api/info/", get_info),
]

urlpatterns += router.urls
