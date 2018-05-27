from django.db import models
import autoslug
from lib import utils
from django.db import connection
from django.utils import timezone


class UserAgent(models.Model):
    agent = models.TextField(unique=True)
    model = models.CharField(max_length=256, null=True)


class DeviceManager(models.Manager):

    def get_queryset(self):
        with connection.cursor() as cursor:
            params = [
                (autoslug.utils.slugify(utils.secure_random_id(None)),
                 entry.id)
                for entry in super(DeviceManager, self).get_queryset().filter(slug=None).iterator()
            ]
            cursor.executemany("UPDATE {} SET slug = %s WHERE id = %s".format(DeviceEntry._meta.db_table), params)

        return super(DeviceManager, self).get_queryset()


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
    slug = autoslug.AutoSlugField(unique=True, populate_from=utils.secure_random_id, always_update=False, null=True)
    changing = models.NullBooleanField(null=True, default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    objects = DeviceManager()
