from rest_framework import serializers
from mail_parser.models import Sis, Alarm


class SisSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sis
        fields = ["id", "name", "gestsis_key"]


class AlarmSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Alarm
        fields = ['id', 'address', 'complement', 'location_wgs84', 'location_lv95', 'type']