from django.db import models


class Sis(models.Model):
    name = models.CharField(max_length=255, unique=True)
    gestsis_key = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name_plural = "sis"

    def __str__(self):
        return self.name

class Alarm(models.Model):
    sis = models.ManyToManyField(Sis)
    address = models.CharField(max_length=255)
    complement = models.CharField(max_length=255)
    location_wgs84 = models.CharField(max_length=255, null=True)
    location_lv95 = models.CharField(max_length=20, null=True)
    couleur = models.CharField(max_length=20, null=True)
    code = models.CharField(max_length=100, null=True)
    type = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=100, default='')
    date_creation = models.DateTimeField(null=True)
    debut_alarme = models.DateTimeField(null=True)
    fin_alarme = models.DateTimeField(null=True)
    # Extra data for management
    has_been_read = models.BooleanField(default=False)

    def __str__(self):
        return self.address

class Group(models.Model):
    sis = models.ForeignKey(Sis, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=20, null=True)
    alarm = models.ForeignKey(Alarm, related_name='groups', on_delete=models.CASCADE)

    def __str__(self):
        return self.number + " " + self.name

class Firefighter(models.Model):
    sis = models.ForeignKey(Sis, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=255)
    group_number = models.CharField(max_length=20, null=True)
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    alarm = models.ForeignKey(Alarm, related_name='firefighters', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fullname', 'sis', 'group_name', 'group_number', 'phone', 'alarm'], name='unique_firefighter')
        ]

    def __str__(self):
        return self.fullname

    def __eq__(self, other):
        if not isinstance(other, Firefighter):
            return NotImplemented

        return self.sis_id == other.sis_id and self.group_name == other.group_name and \
               self.fullname == other.fullname and self.phone == other.phone and \
               self.group_number == self.group_number and self.alarm == self.alarm

class File(models.Model):
    alarm = models.ForeignKey(Alarm, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.filename
