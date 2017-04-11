from django.db import models

class UserAgent(models.Model):
    agent = models.TextField(unique=True)
    model = models.CharField(max_length=256)

class DeviceEntry(models.Model):
    ip = models.CharField(max_length=20, unique=False)
    #overwrite ip with newest one
    mac = models.CharField(max_length=20, null=False, unique=True)
    dhcp_fingerprint = models.CharField(max_length=256, null=True)
    dhcp_vendor = models.CharField(max_length=256, null=True)
    user_agent = models.ManyToManyField(UserAgent)
    hostname = models.CharField(max_length=256, null=True)
    # device_name = models.CharField(max_length=256, null=True)
