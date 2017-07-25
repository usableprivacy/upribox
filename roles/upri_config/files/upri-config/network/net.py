from netaddr import IPNetwork, IPAddress, ZEROFILL
from lib.utils import call_ansible, write_role


# return values:
# 10: invalid argument


def action_set_static_ip(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    arg = "static" if arg == "yes" else "dhcp"
    print 'interface mode: %s' % arg
    en = {"general": {"mode": arg}}
    write_role('interfaces', en)


def action_set_ip(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
    except:
        return 12

    obj = {"static": {"ip": str(ip)}}
    write_role('interfaces', obj)


def action_set_dns_server(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
    except:
        return 12

    obj = {"static": {"dns": str(ip)}}
    write_role('interfaces', obj)


def action_set_netmask(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
        if not ip.is_netmask():
            return 13
    except:
        return 12

    obj = {"static": {"netmask": str(ip)}}
    write_role('interfaces', obj)


def action_set_gateway(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
    except:
        return 12

    obj = {"static": {"gateway": str(ip)}}
    write_role('interfaces', obj)


def action_restart_network(arg):
    print 'restarting network...'
    return call_ansible('network_config')


def action_set_dhcpd(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'DHCP server enabled: %s' % arg
    en = {"general": {"enabled": arg}}
    write_role('dhcpd', en)


def action_restart_dhcpd(arg):
    print 'restarting dhcp server...'
    return call_ansible('dhcp_server')


def action_restart_firewall(arg):
    print 'restarting firewall...'
    return call_ansible('iptables')
