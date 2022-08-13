from rest_framework import serializers
from mail_parser.models import Firefighter, Sis, Alarm, Group

# Serializers used by Django Rest Framework to render model into JSON objects


class SisSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sis
        fields = ["id", "name", "gestsis_key"]


class GroupSerializer(serializers.ModelSerializer):
    sis = serializers.SlugRelatedField(slug_field="gestsis_key", read_only=True)

    class Meta:
        model = Group
        fields = ["name", "number", "sis"]


class FirefighterSerializer(serializers.ModelSerializer):
    sis = serializers.SlugRelatedField(slug_field="gestsis_key", read_only=True)

    class Meta:
        model = Firefighter
        fields = ["fullname", "group_name", "group_number", "phone", "sis"]


class AlarmSerializer(serializers.ModelSerializer):
    sis = serializers.SlugRelatedField(slug_field="gestsis_key", read_only=True, many=True)
    firefighters = FirefighterSerializer(read_only=True, many=True)
    groups = GroupSerializer(read_only=True, many=True)

    class Meta:
        model = Alarm
        fields = ['id', 'address', 'complement', 'location_wgs84', 'location_lv95', 'type', 'sis', 'firefighters', 'groups', 'has_been_read']
