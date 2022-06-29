from django.db import models


class Sis(models.Model):
    name = models.CharField(max_length=255)
    gestsis_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Alarm(models.Model):
    sis = models.ManyToManyField(Sis)
    firefighter = models.ManyToManyField(Firefighter)
    address = models.CharField(max_length=255)
    location_wgs84 = models.CharField(max_length=255)
    location_lv95 = models.CharField(max_length=20)
    type = models.CharField(max_length=100)
    has_been_read = models.BooleanField(default=False)

    def __str__(self):
        return self.id


class Firefighter(models.Model):  # Dans le cas présent, le sapeur est lié à l'alarme...
    alarm_id = models.ForeignKey(Alarm, on_delete=models.CASCADE)
    group = models.CharField(max_length=255)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)

    def __str__(self):
        return self.fullname


class File(models.Model):
    alarm_id = models.ForeignKey(Alarm, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)

    def __str__(self):
        return self.filename

