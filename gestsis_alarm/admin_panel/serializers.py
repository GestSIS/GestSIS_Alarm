from rest_framework import serializers
from mail_parser.models import Sis, Alarm


class SisSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sis
        fields = ["id", "name", "gestsis_key"]


class AlarmSerializer(serializers.ModelSerializer):
    sis = serializers.SlugRelatedField(slug_field="gestsis_key", read_only=True, many=True)

    class Meta:
        model = Alarm
        fields = ['id', 'address', 'complement', 'location_wgs84', 'location_lv95', 'type', 'sis']