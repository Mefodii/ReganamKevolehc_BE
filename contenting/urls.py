from rest_framework import routers
from .api import ContentListViewSet, ContentItemViewSet, ContentTrackViewSet, ContentWatcherViewSet, \
    ContentMusicItemViewSet

router = routers.DefaultRouter()
router.register("api/contentLists", ContentListViewSet, "contentLists")
router.register("api/contentItems", ContentItemViewSet, "contentItems")
router.register("api/contentMusicItems", ContentMusicItemViewSet, "contentMusicItems")
router.register("api/contentTracks", ContentTrackViewSet, "contentTracks")
router.register("api/contentWatchers", ContentWatcherViewSet, "contentWatchers")

urlpatterns = []

urlpatterns += router.urls
