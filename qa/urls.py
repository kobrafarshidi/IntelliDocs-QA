from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import HistoryViewSet, ask

router = DefaultRouter()
router.register(r"history", HistoryViewSet, basename="history")

urlpatterns = [
    path("ask/", ask, name="ask"),
    *router.urls,
]
