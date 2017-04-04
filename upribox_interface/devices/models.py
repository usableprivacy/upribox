from django.db import models

class DeviceEntry(models.Model):
    ip = models.CharField(max_length=20, unique=True)
    mac = models.CharField(max_length=20, null=True)
    dhcp_fingerprint = models.CharField(max_length=256, null=True)
    dhcp_vendor = models.CharField(max_length=256, null=True)
    user_agent = models.CharField(max_length=256, null=True)
    hostname = models.CharField(max_length=256, null=True)
    device_name = models.CharField(max_length=256, null=True)
    final = models.BooleanField(default=False)