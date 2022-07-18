from django.urls import include, path, re_path
from rest_framework import routers
from .views import SisViewSet, AlarmViewSet, AlarmSetterUpdateView

router = routers.DefaultRouter()
router.register(r"sis", SisViewSet)  # GET, POST, PUT, PATCH, DELETE methods automatically created

urlpatterns = [
    path('', include(router.urls)),
    path('alarm/', AlarmViewSet.as_view()),
    re_path(r"^alarm/(?P<pk>\d+)/(?P<has_been_read>[0-1])/$", AlarmSetterUpdateView.as_view())
]