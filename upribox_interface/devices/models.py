from django.db import models

class UserAgent(models.Model):
    ua = models.CharField(max_length=512)

class DeviceName(models.Model):
    name = models.CharField(max_length=256)

class DeviceEntry(models.Model):
    ip = models.CharField(max_length=20, unique=True)
    mac = models.CharField(max_length=20, null=True, unique=True)
    dhcp_fingerprint = models.CharField(max_length=256, null=True)
    dhcp_vendor = models.CharField(max_length=256, null=True)
    user_agent = models.ManyToManyField(UserAgent)
    hostname = models.CharField(max_length=256, null=True)
    device_name = models.ManyToManyField(DeviceName)