from django.contrib import admin
from mail_parser.models import Sis, Alarm, Firefighter, Group, File

# Register your models here.
admin.site.register(Sis)
admin.site.register(Alarm)
admin.site.register(Firefighter)
admin.site.register(Group)
admin.site.register(File)
