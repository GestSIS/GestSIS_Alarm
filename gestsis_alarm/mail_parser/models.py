from django.db import models


class Sis(models.Model):
    name = models.CharField(max_length=255)
    gestsis_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Firefighter(models.Model):
    sis = models.ForeignKey(Sis, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=255)
    group_number = models.CharField(max_length=20, null=True)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fullname', 'sis', 'group_name', 'group_number', 'phone'], name='unique_firefighter')
        ]

    def __str__(self):
        return self.fullname

    def __eq__(self, other):
        if not isinstance(other, Firefighter):
            return NotImplemented

        return self.sis == other.sis and self.group_name == other.group_name and \
               self.fullname == other.fullname and self.phone == other.phone and self.group_number == self.group_name


class Alarm(models.Model):
    sis = models.ManyToManyField(Sis)
    firefighter = models.ManyToManyField(Firefighter)
    address = models.CharField(max_length=255)
    complement = models.CharField(max_length=255)
    location_wgs84 = models.CharField(max_length=255)
    location_lv95 = models.CharField(max_length=20)
    type = models.CharField(max_length=100)
    has_been_read = models.BooleanField(default=False)

    def __str__(self):
        return self.address


class File(models.Model):
    alarm = models.ForeignKey(Alarm, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.filename
