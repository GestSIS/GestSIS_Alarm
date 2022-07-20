from rest_framework import viewsets, generics, views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from mail_parser.models import Sis, Alarm, Firefighter
from django.db.models import Prefetch
from .serializers import SisSerializer, AlarmSerializer
from .permissions import IsAdmin


class SisViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Sis.objects.all()
    serializer_class = SisSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class AlarmViewSet(generics.ListAPIView):
    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # If user has admin rights, they bypass all the filters
        if self.request.user.is_admin:
            return Alarm.objects\
                .prefetch_related(Prefetch('firefighter'))\
                .filter(has_been_read=False)

        # Retrieve SIS where the current user has access to
        keys = self.request.user.get_sis_for_permissions(["intervention.modification"])

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
        ).filter(sis__gestsis_key__in=keys, has_been_read=False)

        return queryset


class AlarmSetterUpdateView(views.APIView):
    """
    Endpoint to change the reading status of an Alarm.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        keys = self.request.user.get_sis_for_permissions(["intervention.modification"])

        model = get_object_or_404(Alarm, pk=pk)

        # The filter could have been done in get_object_or_404 to save a query to the database but it would return 404 error
        # when the user doesn't have to correct permissions
        if not request.user.is_admin:
            user_has_permission = model.sis.filter(gestsis_key__in=keys).exists()
            if not user_has_permission:
                return Response({"message": "Invalid permission to access this object"}, status.HTTP_403_FORBIDDEN)

        has_been_read = request.POST.get("has_been_read")

        if has_been_read not in ["true", "false"]:
            return Response({"message": "Missing/Invalid has_been_read in body"}, status=status.HTTP_400_BAD_REQUEST)

        data = {"has_been_read": has_been_read == "true"}
        serializer = AlarmSerializer(model, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": {"id": model.pk, "has_been_read": model.has_been_read}, "message": "Success", })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
