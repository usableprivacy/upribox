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
import statistics.views

import devices.views
import more.views
import setup.views
import traffic.views
import vpn.views
import wlan.views
import www.views
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

urlpatterns = [

    # www config
    url(r'^help/$', www.views.faq, name="upri_faq"),

    # more config
    # url(r'^more/$', more.views.more_config, {"save_form": "user"}, name="upri_more"),
    url(r'^more/ssh/toggle$', more.views.ssh_toggle, name="upri_ssh_toggle"),
    # automatic mode
    url(r'^more/apate/toggle$', more.views.apate_toggle, name="upri_apate_toggle"),
    # url(r'^more/dhcp$', more.views.save_dhcp, name="upri_dhcp_save"),
    # url(r'^more/static$', more.views.more_config, {"save_form": "static_ip"}, name="upri_static_save"),
    url(r'^more/modal$', more.views.show_modal, name="upri_modal"),

    # new config
    url(r'^config/static$', more.views.more_static, {"enable": True}, name="upri_config_static"),
    url(r'^config/static/enable$', more.views.more_static, {"enable": True}, name="upri_config_static_enable"),
    url(r'^config/static/dhcpd$', more.views.more_static, {"enable": True,
                                                           "dhcpd": True}, name="upri_config_static_dhcpd"),
    url(r'^config/user$', more.views.more_user, name="upri_config_user"),
    url(r'^config/$', more.views.more_overview, name="upri_config"),
    url(r'^config/static/toggle$', more.views.static_toggle, name="upri_static_toggle"),
    # manual mode (dhcpd)
    url(r'^config/manual$', more.views.manual_toggle, name="upri_config_manual"),
    # wifi only mode
    url(r'^config/wifi_only$', more.views.wifi_mode, name="upri_config_wifi"),

    # Auth config
    url(r'^login/$', auth_views.login, {"template_name": "login.html"}, name="upri_login"),
    url(r'^logout/$', auth_views.logout, {"next_page": "upri_login"}, name="upri_logout"),

    # index
    url(r'^$', RedirectView.as_view(pattern_name='upri_devices', permanent=False), name='upri_index'),

    # WLAN config
    url(r'^silent/$', wlan.views.silent, name="upri_silent"),
    url(r'^silent/toggle/$', wlan.views.silent_toggle, name="upri_silent_toggle"),
    # url(r'^ninja/$', wlan.views.ninja, name="upri_ninja"),
    # url(r'^ninja/toggle/$', wlan.views.ninja_toggle, name="upri_ninja_toggle"),

    # jobs
    url(r'^jobstatus/$', www.views.jobstatus, name="upri_jobstatus"),
    url(r'^jobstatus/clear/$', www.views.clear_jobstatus, name="upri_clear_jobstatus"),
    url(r'^jobstatus/count/$', www.views.jobcounter, name="upri_counter_jobstatus"),
    url(r'^jobstatus/failed/$', www.views.jobstatus_failed, name="upri_jobstatus_failed"),
    url(r'^jobstatus/failed/clear/$', www.views.clear_failed, name="upri_clear_failed"),

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
    url(r'^statistics/complete$', statistics.views.json_statistics, name="upri_get_statistics"),
    url(r'^statistics/update(?:/(?P<week>[0-9]{1,2}))?$', statistics.views.statistics_update, name="upri_update_statistics"),
    # url(r'^statistics/update$', statistics.views.statistics_update_without_week, name="upri_update_statistics_without_week"),
    # url(r'^statistics/update/(?:(?P<week>[0-9]{1,2})/)?$', statistics.views.statistics_update, name="upri_update_statistics"),

    # devices
    url(r'^devices/$', devices.views.get_devices, name="upri_devices"),
    url(r'^devices/refresh/$', devices.views.refresh_devices, name="upri_complete_device_list"),
    url(r'^devices/change_mode/$', devices.views.set_device_mode, name="upri_devices_mode"),
    url(r'^devices/change_name/(?P<slug>\w+)$', devices.views.change_name, name="upri_device_name"),
    url(r'^devices/status(?:/(?P<slug>\w+))?$', devices.views.get_device_status, name="upri_device_status"),
    # url(r'^devices/status$', devices.views.get_device_status_without_slug, name="upri_device_status_without_slug"),
    url(r'^devices/processing/$', devices.views.changing_devices, name="upri_in_progress_devices"),
    url(r'^devices/single_device_template', devices.views.single_device_template, name="upri_device_single_device_template"),
    url(r'^devices/entry/$', devices.views.device_entry, name="upri_device_entry"),

    # url(r'^fail/$', devices.views.fail, name="upri_fail"),

    # setup
    url(r'^setup/$', setup.views.setup_init, name="upri_setup"),
    url(r'^setup/evaluation$', setup.views.setup_eval, name="upri_setup_eval"),
    url(r'^setup/error$', setup.views.setup_error, name="upri_setup_error"),
    url(r'^setup/failed$', setup.views.setup_failed, name="upri_setup_failed"),
    url(r'^setup/success$', setup.views.setup_success, name="upri_setup_success"),

    # traffic
    url(r'^traffic/(?P<slug>\w+)(?:/(?P<week>[0-9]{1,2})/(?P<year>[0-9]{4}))?$', traffic.views.get_statistics, name="upri_traffic"),
    url(r'^traffic/domains/(?P<slug>\w+)(?:/(?P<week>[0-9]{1,2}))?$', traffic.views.get_device_queries, name="upri_traffic_domains"),
    url(r'^traffic/overview/(?P<slug>\w+)$', traffic.views.get_overview, name="upri_traffic_overview"),
]
