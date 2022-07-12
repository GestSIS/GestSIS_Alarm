from rest_framework import viewsets
from mail_parser.models import Sis, Alarm
from .serializers import SisSerializer, AlarmSerializer


class SisViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Sis.objects.all()
    serializer_class = SisSerializer


class AlarmViewSet(viewsets.ModelViewSet):
    queryset = Alarm.objects.all()
    serializer_class = AlarmSerializer
