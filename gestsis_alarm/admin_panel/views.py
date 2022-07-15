from rest_framework import viewsets
from mail_parser.models import Sis, Alarm, Firefighter
from django.db.models import Prefetch
from .serializers import SisSerializer, AlarmSerializer


class SisViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Sis.objects.all()
    serializer_class = SisSerializer


class AlarmViewSet(viewsets.ModelViewSet):
    serializer_class = AlarmSerializer

    def get_queryset(self):
        # Should change based on the authenticated user
        keys = ["ca"]

        # Django is quite annoying sometimes. For example, in a Many to Many relationship,
        # you would think a simple filter like that would work :
        # queryset = Alarm.objects.filter(sis__gestsis_key=key, firefighter__sis__gestsis_key=key)
        # It doesn't ! Even thought, a lot of example in the django documentation tell otherwise.
        # It's simply because you need to prefetch the data in the other end of the M2M relationship
        # and apply it directly. A simple `prefetch_related` and after the filter method won't work !
        # You need to include the filter for the nested table in the prefetch !!
        # My lifesaver : https://stackoverflow.com/a/55315566
        queryset = Alarm.objects.prefetch_related(
            Prefetch(
                'firefighter',
                queryset=Firefighter.objects.filter(sis__gestsis_key__in=keys)
            )
        ).filter(sis__gestsis_key__in=keys)

        return queryset
