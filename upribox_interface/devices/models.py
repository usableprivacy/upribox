from django.db import models

class UserAgent(models.Model):
    agent = models.TextField(unique=True)
    model = models.CharField(max_length=256, null=True)

class DeviceEntry(models.Model):
    ip = models.CharField(max_length=20, unique=False)
    mac = models.CharField(max_length=20, null=False, unique=True)
    dhcp_fingerprint = models.CharField(max_length=256, null=True)
    dhcp_vendor = models.CharField(max_length=256, null=True)
    user_agent = models.ManyToManyField(UserAgent)
    hostname = models.CharField(max_length=256, null=True)
    MODES = (
        ('SL', "Silent"),
        ('NJ', "Ninja"),
        ('NO', "No Mode")
    )
    mode = models.CharField(max_length=2, choices=MODES, default='SL')
    chosen_name = models.CharField(max_length=256, null=True)
