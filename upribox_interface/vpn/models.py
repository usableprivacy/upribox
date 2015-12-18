from django.db import models
import autoslug
from lib import utils
class VpnProfile(models.Model):
    profilename = models.CharField(max_length=32)
    config = models.TextField()
    creation_date = models.DateField(auto_now_add=True)
    # first slug - this field is used to reference the object, e.g. when creating a download link or when deleting
    slug = autoslug.AutoSlugField(unique=True, populate_from=utils.secure_random_id)
    # second slug - this field is used for the download link
    download_slug = autoslug.AutoSlugField(unique=True, populate_from=utils.secure_random_id, always_update=True, null=True)
    download_valid_until = models.DateTimeField(null=True)
    dyndomain = models.CharField(max_length=256)

    class Meta:
        ordering = ["creation_date"]
