from django.db import models

class PrivoxyLogEntry(models.Model):
    url = models.CharField(max_length=256)
    log_date = models.DateTimeField()

    class Meta:
        ordering = ["log_date"]
