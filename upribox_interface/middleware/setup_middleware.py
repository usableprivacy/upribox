import redis as redisDB
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings


class SetupMiddleware(object):

    # syntax for keys in redis db for statistics

    def __init__(self, get_response):
        self.get_response = get_response
        self.redis = redisDB.StrictRedis(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"], db=settings.REDIS["DB"])
        self.no_redirect = [reverse(url) for url in settings.SETUP_NO_REDIRECT]
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        if (not self.redis.get(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY))) and
                request.path not in self.no_redirect):
            return HttpResponseRedirect(reverse("upri_setup"))
        else:
            response = self.get_response(request)

            # Code to be executed for each request/response after
            # the view is called.

            return response
