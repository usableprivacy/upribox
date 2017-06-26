#! /bin/bash

if [ ! -f /var/run/wlan_stick.lock ]; then
    touch /var/run/wlan_stick.lock
    /usr/bin/python -u /usr/local/bin/ansible-playbook -i {{ pull_workdir }}/environments/{{ "development" if env == "development" else "production" }}/inventory_pull -c local {{ pull_workdir }}/local.yml --tags wlan_device -v
fi

exit 0
