import json
import subprocess
import os
import sqlite3
import sys
from network.utils import check_domain
from lib.settings import CLIENT_TEMPLATE
from lib.utils import write_role, call_ansible

sys.path.insert(0, "/usr/share/nginx/www-upri-interface/lib/")



#
# revokes previously generated openvpn client certificates
# return values:
# 26 failed to revoke certificate


def action_delete_profile(slug):
    try:
        filename = os.path.basename(slug)

        rc = subprocess.call(['/usr/bin/openssl', 'ca', '-revoke', '/etc/openvpn/ca/%sCert.pem' % filename])
        rc = subprocess.call(['/usr/bin/openssl', 'ca', '-gencrl', '-crlhours', '1', '-out', '/etc/openssl/demoCA/crl.pem'])

        #os.remove('/etc/openvpn/ca/%sKey.pem' % filename)
        #os.remove('/etc/openvpn/ca/%sCert.pem' % filename)

    except Exception as e:
        print "failed to delete client files"
        print str(e)
        return 26

    return 0

#
# generate openvpn client certificates and saves the
# generated openvpn client config into the database
# return values:
# 16: database error
# 21: entry does not exists in database
# 24: provided domain is not valid
# 23: unable to create client certificate files
# 22: openvpn client template is missing


def action_generate_profile(profile_id):
    import domain
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)

    dbfile = config['django']['db']

    try:
        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        c.execute("SELECT slug,dyndomain FROM vpn_vpnprofile WHERE id=?", (profile_id,))
        data = c.fetchone()
        if not data:
            # invalid profile id
            print 'profile id does not exist in database'
            return 21

        slug = data[0]
        dyndomain = data[1]

        if not check_domain(dyndomain):
            return 24

        dyndomain = domain.Domain(data[1]).get_match()

        filename = os.path.basename(slug)

        rc = subprocess.call(['/usr/bin/openssl', 'req', '-newkey', 'rsa:2048', '-nodes', '-subj', "/C=AT/ST=Austria/L=Vienna/O=Usable Privacy Box/OU=VPN/CN=%s" %
                              filename, '-keyout', '/etc/openvpn/ca/%sKey.pem' % filename, '-out', '/etc/openvpn/ca/%sReq.pem' % filename])

        os.chmod('/etc/openvpn/ca/%sKey.pem' % filename, 0640)

        if rc != 0:
            print "error while creating client certificate reques"
            return 23

        subprocess.call(['/usr/bin/openssl', 'ca', '-in', '/etc/openvpn/ca/%sReq.pem' % filename, '-days', '730', '-batch', '-out', '/etc/openvpn/ca/%sCert.pem' %
                         filename, '-notext', '-cert', '/etc/openvpn/ca/caCert.pem', '-keyfile', '/etc/openvpn/ca/caKey.pem'])

        if rc != 0:
            print "error while creating client certificate"
            return 23

        os.remove('/etc/openvpn/ca/%sReq.pem' % filename)

        if os.path.isfile(CLIENT_TEMPLATE):
            with open(CLIENT_TEMPLATE, 'r') as template, open('/etc/openvpn/ca/%sKey.pem' % filename, 'r') as client_key, open('/etc/openvpn/ca/%sCert.pem' % filename, 'r') as client_cert:
                temp = template.read()
                temp = temp.replace("#CLIENT_KEY", client_key.read())
                temp = temp.replace("#CLIENT_CERT", client_cert.read())
                temp = temp.replace("<IP-ADRESS>", dyndomain)

                c.execute("UPDATE vpn_vpnprofile SET config=? where id=?", (temp, profile_id))
                conn.commit()
        else:
            print "client template is missing"
            return 22

        conn.close()
    except Exception as e:
        print "failed to write to database"
        print str(e)
        return 16
    return 0

# return values:
# 10: invalid argument


def action_set_vpn(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'vpn enabled: %s' % arg
    vpn = {"general": {"enabled": arg}}
    write_role('vpn', vpn)
    return 0

# return values:
# 10: invalid argument


def action_set_vpn_connection(arg):
    '1194/udp'
    port, protocol = arg.split('/')
    protocol = protocol.upper()
    if not int(port) in range(1025, 65535) or protocol not in ['UDP', 'TCP']:
        print 'error: only valid "port/protocol" combinations are allowed e.g. "1194/UDP"'
        print 'port must be unprivileged: 1025 - 65535'
        print 'protocol can be either UDP or TCP'
        return 10
    print 'vpn connection: %s' % arg
    vpn_connection = {"connection": {"port": port, "protocol": protocol}}
    write_role('vpn', vpn_connection)
    return 0


def action_restart_vpn(arg):
    print 'restarting vpn...'
    return call_ansible('toggle_vpn')
