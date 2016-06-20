#!/usr/bin/env python
import json
import sys
import subprocess
from jsonmerge import merge
from os import path
import sys
sys.path.insert(0, "/usr/share/nginx/www-upri-interface/lib/")
import passwd 
import ssid
import domain
import re
from datetime import datetime
from urlparse import urlparse
import os
import sqlite3

# directory where facts are located
FACTS_DIR = "/etc/ansible/facts.d"
# path to the ansible-playbook executeable
ANSIBLE_COMMAND = "/usr/local/bin/ansible-playbook"
# path to the used inventory
ANSIBLE_INVENTORY = "/var/lib/ansible/local/environments/production/inventory_pull"
# path to the used playbook
ANSIBLE_PLAY = "/var/lib/ansible/local/local.yml"
# path to the openvpn client config template
CLIENT_TEMPLATE = "/etc/openvpn/client_template" 

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
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)
    
    dbfile = config['django']['db']
    
    try:
        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        c.execute("SELECT slug,dyndomain FROM vpn_vpnprofile WHERE id=?",(profile_id,))
        data = c.fetchone()
        if not data:
            #invalid profile id
            print 'profile id does not exist in database'
            return 21

        slug = data[0]
        dyndomain = data[1]
        
        if not check_domain(dyndomain):
            return 24
        
        dyndomain = domain.Domain(data[1]).get_match()
        
        filename = os.path.basename(slug)
        
        rc = subprocess.call(['/usr/bin/openssl', 'req', '-newkey', 'rsa:2048', '-nodes', '-subj', "/C=AT/ST=Austria/L=Vienna/O=Usable Privacy Box/OU=VPN/CN=%s" % filename, '-keyout', '/etc/openvpn/ca/%sKey.pem' % filename, '-out', '/etc/openvpn/ca/%sReq.pem' % filename])

        if rc != 0:
            print "error while creating client certificate reques"
            return 23
        
        subprocess.call(['/usr/bin/openssl', 'ca', '-in', '/etc/openvpn/ca/%sReq.pem' % filename, '-days', '730', '-batch', '-out', '/etc/openvpn/ca/%sCert.pem' % filename, '-notext', '-cert', '/etc/openvpn/ca/caCert.pem', '-keyfile', '/etc/openvpn/ca/caKey.pem'])
        
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

#
# parse the privoxy logfiles and insert data into django db
# return values:
# 16: database error
# 20: new entries have been added
def action_parse_logs(arg):
    rlog = re.compile('(\d{4}-\d{2}-\d{2} (\d{2}:?){3}).\d{3} [a-z0-9]{8} Crunch: Blocked: (.*)')
    
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)
        
    dbfile = config['django']['db']
    logfile = os.path.join(config['log']['general']['path'], config['log']['privoxy']['subdir'], config['log']['privoxy']['logfiles']['logname'])

    if os.path.isfile(logfile):
        print "parsing privoxy logfile %s" % logfile
        with open(logfile, 'r') as privoxy:
            logentries = []
            for line in privoxy:
                try:
                    res = re.match(rlog, line)
                    if res:
                        sdate = res.group(1)
                        ssite = res.group(3)
                        pdate = datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S')
                        psite = urlparse(ssite).netloc
                        logentries.append( (psite,pdate) )
                        print "found new block: [%s] %s" % (sdate,psite)
                except Exception as e:
                    print "failed to parse line \"%s\": %s" % (line, e.message)
                    
        #write updates into db
        if len(logentries) > 0:
            try:
                conn = sqlite3.connect(dbfile)
                c = conn.cursor()
                c.executemany("INSERT INTO statistics_privoxylogentry(url,log_date) VALUES (?,?)", logentries)
                c.execute("DELETE FROM statistics_privoxylogentry WHERE log_date <= date('now','-6 month')")
                conn.commit()
                conn.close()
                # delete logfile
                os.remove(logfile)
                # todo: implement reload
                subprocess.call(["/usr/sbin/service", "privoxy", "restart"])
            except Exception as e:
                print "failed to write to database"
                return 16
            return 20
    
    else:
        print "failed to parse privoxy logfile %s: file not found" % logfile
        return 0
        
# 
# set a new ssid for the upribox "silent" wlan
# return values:
# 12: ssid does not meet policy
#
def action_set_ssid(arg):
    print 'setting ssid to "%s"' % arg
    if not check_ssid(arg):
        return 12
    ssid = { "upri": { "ssid": arg } }
    write_role('wlan', ssid)

# return values:
# 11: password does not meet password policy
def action_set_password(arg):
    print 'setting password'
    if not check_passwd(arg):
        return 11
    passwd = { "upri": { "passwd": arg } }
    write_role('wlan', passwd)

#
# return values:
# 12: ssid does not meet policy
#
def action_set_tor_ssid(arg):
    print 'setting tor ssid to "%s"' % arg
    if not check_ssid(arg):
        return 12
    ssid = { "ninja": { "ssid": arg } }
    write_role('wlan', ssid)

# return values:
# 11: password does not meet password policy
def action_set_tor_password(arg):
    print 'setting tor password'
    if not check_passwd(arg):
        return 11
    passwd = { "ninja": { "passwd": arg } }
    write_role('wlan', passwd)
    
def action_restart_wlan(arg):
    print 'restarting wlan...'
    return call_ansible('ssid')

# return values:
# 10: invalid argument
def action_set_tor(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'tor enabled: %s' % arg
    passwd = { "general": { "enabled": arg } }
    write_role('tor', passwd)
    
def action_restart_tor(arg):
    print 'restarting tor...'
    return call_ansible('toggle_tor')

# return values:
# 10: invalid argument
def action_set_vpn(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'vpn enabled: %s' % arg
    vpn = { "general": { "enabled": arg } }
    write_role('vpn', vpn)
    return 0

def action_restart_vpn(arg):
    print 'restarting vpn...'
    #return 0 # TODO implement
    return call_ansible('toggle_vpn')

# return values:
# 10: invalid argument
def action_set_ssh(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'ssh enabled: %s' % arg
    en = { "general": { "enabled": arg } }
    write_role('ssh', en)
    
def action_restart_ssh(arg):
    print 'restarting ssh...'
    return call_ansible('toggle_ssh')
    
def check_passwd(arg):
    pw = passwd.Password(arg)
    if not pw.is_valid():
        if not pw.has_digit():
            print 'the password must contain at least 1 digit'
        if not pw.has_lowercase_char():
            print 'the password must contain at least 1 lowercase character'
        if not pw.has_uppercase_char():
            print 'the password must contain at least 1 uppercase character'
        if not pw.has_symbol():
            print 'the password must contain at least 1 special character'
        if not pw.has_allowed_length():
            print 'the password must be between 8 to 63 characters long'
        if not pw.has_only_allowed_chars():
            print 'the password must only contain following special characters: %s' % pw.get_allowed_chars()
            
        return False
    else:
        return True
    
def check_ssid(arg):
    ssid_value = ssid.SSID(arg)
    if not ssid_value.is_valid():
        if not ssid_value.has_allowed_length():
             print 'the password must be between 1 to 32 characters long'
        if not ssid_value.has_only_allowed_chars():
            print 'the ssid must only contain following special characters: %s' % ssid_value.get_allowed_chars()
            
        return False
    else:
        return True
    
def check_domain(arg):
    domain_value = domain.Domain(arg)
    if not domain_value.is_valid():
        if not domain_value.has_allowed_length():
             print 'the password can only contain up to 255 characters'
        if not domain_value.has_only_allowed_chars():
            print 'the domain must only contain following special characters: %s' % domain_value.get_allowed_chars()
            
        return False
    else:
        return True

def action_restart_network(arg):
    print 'restarting network...'
    #return 0 # TODO implement
    return call_ansible('network_config')
    
# add your custom actions here
ALLOWED_ACTIONS = {
    'set_ssid': action_set_ssid,
    'set_password': action_set_password,
    'set_tor_ssid': action_set_tor_ssid,
    'set_tor_password': action_set_tor_password,
    'restart_wlan': action_restart_wlan,
    'enable_tor': action_set_tor,
    'restart_tor': action_restart_tor,
    'enable_vpn': action_set_vpn,
    'restart_vpn': action_restart_vpn,
    'enable_ssh': action_set_ssh,
    'restart_ssh': action_restart_ssh,
    'parse_logs': action_parse_logs,
    'generate_profile': action_generate_profile,
    'delete_profile': action_delete_profile,
    'restart_network': action_restart_network
}

#
# calls ansible and executes the given tag locally
#
def call_ansible(tag):
    return subprocess.call([ANSIBLE_COMMAND, '-i', ANSIBLE_INVENTORY, ANSIBLE_PLAY, "--tags", tag, "--connection=local"])

# 
# write the custom json "data" to the fact with the given name "rolename"
#
def write_role(rolename, data):
    p = path.join(FACTS_DIR, rolename + '.fact')
    try:
        with open(p, 'r') as data_file:
            js = json.load(data_file)
    except IOError:
        js = {}

    js = merge(js, data)
    with open(p, 'w+') as data_file:
        json.dump(js, data_file, indent=4)

# return values:
# 0: ok
# 1: syntax error
# 2: invalid number of arguments
# 3: invalid action
def main():
    # append empty second parameter if none given
    if len(sys.argv) == 2:
        sys.argv.append('')
        
    if len(sys.argv) !=3:
        usage(2)

    action = sys.argv[1]
    args = sys.argv[2]

    # check if requested action is valid
    if sys.argv[1] in ALLOWED_ACTIONS:
        print "action: %s" % action
        return ALLOWED_ACTIONS[action](args)
    else:
        usage(3)

def usage(ex):
    print "usage: %s <action> <args>" % sys.argv[0]
    print "allowed actions:"
    for action in ALLOWED_ACTIONS:
        print "    %s" % action
    exit(ex)


if __name__ == "__main__":
    exit(main())
