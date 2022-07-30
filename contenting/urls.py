from django.urls import path

from rest_framework import routers
from .api import ContentListViewSet, ContentItemViewSet, ContentItemPartViewSet, ContentWatcherViewSet
from .views import get_info

router = routers.DefaultRouter()
router.register("api/contentLists", ContentListViewSet, "contentLists")
router.register("api/contentItems", ContentItemViewSet, "contentItems")
router.register("api/contentItemParts", ContentItemPartViewSet, "contentItemParts")
router.register("api/contentWatchers", ContentWatcherViewSet, "contentWatchers")

urlpatterns = [
    path("api/info/", get_info),
]

urlpatterns += router.urls
