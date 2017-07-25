from lib.utils import write_role, call_ansible
from network.utils import check_ssid, check_passwd

#
# set a new ssid for the upribox "silent" wlan
# return values:
# 12: ssid does not meet policy
#


def action_set_ssid(arg):
    print 'setting ssid to "%s"' % arg
    if not check_ssid(arg):
        return 12
    ssid = {"upri": {"ssid": arg}}
    write_role('wlan', ssid)

# return values:
# 11: password does not meet password policy


def action_set_password(arg):
    print 'setting password'
    if not check_passwd(arg):
        return 11
    passwd = {"upri": {"passwd": arg}}
    write_role('wlan', passwd)


def action_restart_wlan(arg):
    print 'restarting wlan...'
    return call_ansible('ssid')

# return values:
# 10: invalid argument


def action_set_silent(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'silent enabled: %s' % arg
    silent = {"general": {"enabled": arg}}
    write_role('wlan', silent)


def action_restart_silent(arg):
    print 'restarting silent...'
    return call_ansible('toggle_silent')

# return values:
# 10: invalid argument


def action_set_wlan_channel(arg):
    if not int(arg) in range(1, 10):
        print 'error: channel must be between 1 and 10'
        return 10
    print 'wifi channel: %s' % arg
    channel = {"general": {"channel": arg}}
    write_role('wlan', channel)
    return 0
