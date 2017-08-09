import json
import sys
import logging
sys.path.insert(0, "/opt/apate/lib/")
from network.utils import check_ip, get_network, check_mac
from lib.settings import CONFIG_FILE
from lib.utils import write_role, call_ansible


# def action_disable_device(arg):
#     if not check_ip(arg):
#         return 27
#
#     return toggle_device(arg, False)
#
#
# def action_enable_device(arg):
#     if not check_ip(arg):
#         return 27
#
#     return toggle_device(arg, True)


def toggle_device(mac, ip, enabled):
    from apate_redis import ApateRedis
    if not check_ip(ip) or not check_mac(mac):
        return 27

    try:
        with open(CONFIG_FILE) as config:
            data = json.load(config)
    except ValueError as ve:
        print "Could not parse the configuration file"
        print str(ve)
        return 28
    except IOError as ioe:
        print "An error occurred while trying to open the configuration file"
        print str(ioe)
        return 29

    if 'interface' not in data:
        print "The configuration file does not include all necessary options"
        return 30

    network = get_network(data['interface'], check_ip(ip))
    if not network:
        return 31

    try:
        redis = ApateRedis(network, logging.getLogger('config'))
        if enabled:
            redis.enable_device(mac, ip, network)
        else:
            redis.disable_device(mac, ip, network)
    except:
        return 32

    return 0


def action_set_apate(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'apate enabled: %s' % arg
    en = {"general": {"enabled": arg}}
    write_role('apate', en)


def action_restart_apate(arg):
    print 'restarting apate...'
    return call_ansible('toggle_apate')
