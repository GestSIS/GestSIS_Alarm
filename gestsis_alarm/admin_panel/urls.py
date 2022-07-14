
from django.urls import include, path
from rest_framework import routers
from .views import SisViewSet, AlarmViewSet

router = routers.DefaultRouter()
router.register(r"sis", SisViewSet)
router.register(r"alarm", AlarmViewSet, basename="alarm")

urlpatterns = [
    path('', include(router.urls))
]