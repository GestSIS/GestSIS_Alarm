
from django.urls import include, path, re_path
from rest_framework import routers
from .views import SisViewSet, AlarmViewSet, AlarmSetterUpdateView

router = routers.DefaultRouter()
router.register(r"sis", SisViewSet)
router.register(r"alarm", AlarmViewSet, basename="alarm")

urlpatterns = [
    path('', include(router.urls)),
    re_path(r"^alarm/(?P<pk>\d+)/(?P<has_been_read>[0-1])/$", AlarmSetterUpdateView.as_view())
]