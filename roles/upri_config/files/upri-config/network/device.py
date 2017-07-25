import logging
from network.utils import check_ip, check_mac
from lib.utils import call_ansible, write_role, get_fact

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
# import traceback


def action_check_device(arg):
    # import inside function, because import is slow
    from scapy.all import arping
    if not check_ip(arg):
        return False

    return bool(len(arping(arg, iface=None, verbose=0)[0]))


def action_configure_devices(arg):
    print 'configuring devices...'
    return call_ansible('configure_devices')


def _config_mac(group, mac, remove=False):
    if check_mac(mac):
        devices = get_fact('devices', group) or []
        if not remove and mac.lower() not in devices:
            devices.append(mac.lower())
        elif remove and mac.lower() in devices:
            devices.remove(mac.lower())
        en = {group: devices}
        write_role('devices', en)
    else:
        return 30


def action_torify_device(arg):
    if _config_mac("tor", arg):
        print 'error: invalid mac address'
        return 30
    # remove from other list
    print 'torified device: %s' % arg
    action_include_device(arg)


def action_exclude_device(arg):
    if _config_mac("no_adblocking", arg):
        print 'error: invalid mac address'
        return 30
    # remove from other list
    print 'excluded device: %s' % arg
    action_untorify_device(arg)


def action_include_device(arg):
    if _config_mac("no_adblocking", arg, remove=True):
        print 'error: invalid mac address'
        return 30
    print 'included device: %s' % arg


def action_untorify_device(arg):
    if _config_mac("tor", arg, remove=True):
        print 'error: invalid mac address'
        return 30
    print 'untorified device: %s' % arg


def action_silent_device(arg):
    if check_mac(arg):
        action_include_device(arg)
        action_untorify_device(arg)
    else:
        print 'error: invalid mac address'
        return 30
