from rest_framework import viewsets, generics, views, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from mail_parser.models import Sis, Alarm, Firefighter
from django.db.models import Prefetch
from .serializers import SisSerializer, AlarmSerializer
from .permissions import IsAdmin
from django.core.management import call_command

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
        sis_id = self.request.META.get("HTTP_SIS_ID")
        keys = None

        if self.request.user.is_admin:
            if sis_id:
                keys = [sis_id]
            else:
                keys = "all"
        else:
            perms = self.request.user.get_sis_for_permissions(["intervention.modification"])
            if sis_id:
                if sis_id not in perms:
                    raise PermissionDenied({"message": "Insufficient permission to retrieve the SIS data specified"})

                keys = [sis_id]
            else:
                keys = perms

        # Force update of the database before retrieving data
        if "force_update" in self.request.query_params:
            call_command("mail_and_extract")

        if keys == "all":
            return Alarm.objects\
                    .prefetch_related(Prefetch('firefighters'))\
                    .filter(has_been_read=False)

        # The prefetching here is done because you can't filter a M2M relationship directly without the data being there.
        # The filter in the prefetch is really important because otherwise, it won't work and you would have all firefighter attached to this alarm.
        # You might find MANY examples in the official Django Documentation that shows you that you can do it without prefetching, but they are wrong.
        # https://stackoverflow.com/a/55315566
        queryset = Alarm.objects.prefetch_related(
            Prefetch(
                'firefighters',
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
