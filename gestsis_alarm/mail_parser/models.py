from django.db import models


class Sis(models.Model):
    name = models.CharField()
    gestsis_name = models.CharField()


class Alarm(models.Model):
    sis_id = models.ForeignKey(Sis, on_delete=models.CASCADE)
    address = models.CharField()
    location_wgs84 = models.CharField()
    location_lv95 = models.CharField(max_length=20)
    type = models.CharField()
    has_been_read = models.BooleanField(default=False)


class Firefighter(models.Model):  # Dans le cas présent, le sapeur est lié à l'alarme...
    alarm_id = models.ForeignKey(Alarm, on_delete=models.CASCADE)
    group = models.CharField()
    fullname = models.CharField()
    phone = models.CharField(max_length=50)


class File(models.Model):
    alarm_id = models.ForeignKey(Alarm, on_delete=models.CASCADE)
    filename = models.CharField()

