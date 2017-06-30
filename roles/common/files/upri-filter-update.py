#!/usr/bin/env python

import json
import os
import requests
from requests.exceptions import ConnectionError, Timeout, SSLError
import hashlib
import subprocess
import sys
import traceback

# path to the json file that contains the urls from where updates are loaded
UPDATE_INFO_FILE = "/usr/local/etc/upri-filter-update/updates.json"
# path to the pem file that contains the servers cert (for certificate pinning)
SSL_PINNING_PATH = "/usr/local/etc/upri-filter-update/update-server.pem"

# maximum number of attempts to retry on io errors when downloading files
MAX_ATTEMPTS = 3
# this postfix is prepended to all update urls to get the sha256
UPDATE_URL_POSTFIX = ".sha256"
# whiteliste of services that can be restarted
RESTART_WHITELIST = {
    "restart-dnsmasq": ["/usr/sbin/service", "dnsmasq", "restart"],
    "restart-dnsmasq-ninja": ["/usr/sbin/service", "dnsmasq-ninja", "restart"],
    "restart-nginx": ["/usr/sbin/service", "nginx", "reload"],
    "generate-tor-blocklist": ["/bin/bash", "-c", "/bin/sed 's/\.55\./\.56\./' /etc/dnsmasq.d/dnsblacklist.conf > /etc/dnsmasq.d.ninja/dnsblacklist.conf"]
}


def download_file(url):

    attempts = 0
    while True:
        try:
            resp = requests.get(url, verify=SSL_PINNING_PATH)
            resp.raise_for_status()
            return resp.content
        # retry 3 times on DNS failure, refused connection, ...
        except (ConnectionError, Timeout) as e:
            print "error getting %s: %s " % (url, e.message)
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
                raise e


def hash_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, 'r') as f:
        hsh = hashlib.sha256()
        hsh.update(f.read())
        return hsh.hexdigest()


def main():
    if os.path.isfile(UPDATE_INFO_FILE):

        exit_code = 0
        to_restart = list()

        with open(UPDATE_INFO_FILE, 'r') as f:
            updates = json.load(f)

        for update in updates:
            update_from = update.get('update_from', None)
            update_to = update.get('update_to', None)
            restart = update.get('run', [])
            sha256 = hash_file(update_to)

            print "checking updates for %s" % update_to

            # download current sha
            newsha256 = download_file(update_from + UPDATE_URL_POSTFIX)

            # check if update is required
            if not sha256 or sha256 != newsha256:
                exit_code = 1
                print 'new update detected, downloading...'
                updated_file = download_file(update_from)

                # write new file
                if not os.path.exists(os.path.dirname(update_to)):
                    os.makedirs(os.path.dirname(update_to))

                with open(update_to, 'w') as outf:
                    outf.write(updated_file)

                for service in restart:
                    if service not in to_restart:
                        to_restart.append(service)

        if(len(to_restart) > 0):
            print "updated complete, restarting services..."

        for restart in to_restart:
            if restart and restart in RESTART_WHITELIST:
                print "executing %s" % (restart)
                rc = subprocess.call(RESTART_WHITELIST[restart])
                if rc != 0:
                    print "restarting of %s failed" % restart
        print "done"
        return exit_code
    else:
        return 4

if __name__ == "__main__":
    try:
        exit_code = main()
    except:
        traceback.print_exc(file=sys.stdout)
        exit(2)
    exit(exit_code)
