"""webapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
import more.views
import www.views
import wlan.views
import vpn.views
import statistics.views
import devices.views

urlpatterns = [

    # www config
    url(r'^help/$', www.views.faq, name="upri_faq"),

    # more config
    url(r'^more/$', more.views.more_config, {"save_form": "user"}, name="upri_more"),
    url(r'^more/ssh/toggle$', more.views.ssh_toggle, name="upri_ssh_toggle"),
    url(r'^more/apate/toggle$', more.views.apate_toggle, name="upri_apate_toggle"),
    url(r'^more/dhcp$', more.views.save_dhcp, name="upri_dhcp_save"),
    url(r'^more/static$', more.views.more_config, {"save_form": "static_ip"}, name="upri_static_save"),

    # Auth config
    url(r'^login/$', auth_views.login, {"template_name": "login.html"}, name="upri_login"),
    url(r'^logout/$', auth_views.logout, {"next_page": "upri_login"}, name="upri_logout"),

    # WLAN config
    url(r'^$', RedirectView.as_view(pattern_name='upri_silent', permanent=False), name='upri_index'),
    url(r'^silent/$', wlan.views.silent, name="upri_silent"),
    url(r'^silent/toggle/$', wlan.views.silent_toggle, name="upri_silent_toggle"),
    url(r'^ninja/$', wlan.views.ninja, name="upri_ninja"),
    url(r'^ninja/toggle/$', wlan.views.ninja_toggle, name="upri_ninja_toggle"),
    url(r'^jobstatus/$', www.views.jobstatus, name="upri_jobstatus"),
    url(r'^jobstatus/clear/$', www.views.clear_jobstatus, name="upri_clear_jobstatus"),

    # VPN config
    url(r'^vpn/$', vpn.views.vpn_config, name="upri_vpn"),
    url(r'^vpn/toggle/$', vpn.views.vpn_toggle, name="upri_vpn_toggle"),
    url(r'^vpn/check_connection/$', vpn.views.check_connection, name="upri_check_connection"),
    url(r'^vpn/generate/$', vpn.views.vpn_generate, name="upri_vpn_generate"),
    url(r'^vpn/delete/(?P<slug>\w+)$', vpn.views.vpn_delete, name="upri_vpn_delete"),
    url(r'^vpn/(?P<download_slug>\w+)/upribox.ovpn$', vpn.views.vpn_download, name="upri_vpn_download"),
    url(r'^vpn/createlink/(?P<slug>\w+)$', vpn.views.vpn_create_download, name="upri_vpn_create_download"),
    url(r'^vpn/get/(?P<slug>\w+)$', vpn.views.vpn_get, name="upri_vpn_get"),

    # statistics config
    url(r'^statistics/$', statistics.views.get_statistics, name="upri_statistics"),
    url(r'^statistics/get$', statistics.views.json_statistics, name="upri_get_statistics"),

    # devices
    url(r'^devices/$', devices.views.get_devices, name="upri_devices"),
    url(r'^devices/change_mode/$', devices.views.set_device_mode, name="upri_devices_mode")

]
