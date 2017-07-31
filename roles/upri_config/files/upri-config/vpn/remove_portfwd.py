import miniupnpc
import subprocess

from lib.utils import check_fact

# Port for OpenVPN
PORT = check_fact('vpn', 'connection', 'port', debug=False)
PROTOCOL = check_fact('vpn', 'connection', 'protocol', debug=False)

debug = False


def action_remove_forward(arg):
    if arg == True:
        global debug
        debug = True

    # Check if UPNP is available
    upnpc = miniupnpc.UPnP()

    # Discover UPNP devices
    upnpc.discoverdelay = 200

    if debug:
        print 'Check UPNP Support'

    pub_ip = None
    try:
        ndevices = upnpc.discover()
        if debug:
            print ' %d UPNP device(s) detected' % (ndevices)

        if ndevices:
            upnpc.selectigd()
            pub_ip = upnpc.externalipaddress()

    except Exception:
        if debug:
            print ' No appropriate UPNP device available'

    # If UPNP device with public IP is found activate port forwarding
    if pub_ip:
        if debug:
            print ' internal ip: ', upnpc.lanaddr
            print ' external ip: ', pub_ip
            print ' status: %s, connection type: %s' % (upnpc.statusinfo(), upnpc.connectiontype())

            # Check current port mapping status
        try:
            r = upnpc.getspecificportmapping(PORT, PROTOCOL)

            if 'upri.box OpenVPN port' in r[2]:
                if debug:
                    print ' Delete port forwarding with UPNP'

                r = upnpc.deleteportmapping(PORT, PROTOCOL)
                if debug:
                    if r is None:
                        print ' Successful deleted'
        except Exception:
            if debug:
                print '  Execption: UPNP port forwarding cannot be deleted'

    # Check NATPMP support
    else:
        try:
            if debug:
                print 'Check NATPMP Support'

            natpmp_chk = 'natpmpc'
            p = subprocess.Popen(natpmp_chk, stdout=subprocess.PIPE, stderr=None)
            retcode = p.wait()
            status = p.communicate()[0]

            if debug:
                print ' NATPMP Status:'
                print status

            # If NATPMP avaiable - enable port forwarding
            if ('readnatpmpresponseorretry returned 0' in status):
                if debug:
                    print ' Delete port forwarding with NATPMP'
                natpmp_en = ['natpmpc', '-a', str(PORT), str(PORT), PROTOCOL, '0']

                p = subprocess.Popen(natpmp_en, stdout=subprocess.PIPE, stderr=None)
                retcode = p.wait()
                status = p.communicate()[0]

                if debug:
                    print status

        except Exception, e:
            if debug:
                print '  Execption: UPNP port forwarding cannot be deleted: ', e
            return 1

        return 0
