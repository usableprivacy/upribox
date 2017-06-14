#! /bin/sh

#pgrep ansible

if [ ! -f /var/run/wlan.lock ]; then
    touch /var/run/wlan.lock
    case $IFACE in
        *wlan*) nohup /usr/local/bin/ansible-playbook -i {{ pull_workdir }}/environments/{{ "development" if env == "development" else "production" }}/inventory_pull -c local {{ pull_workdir }}/local.yml --tags wlan_device &> /home/upri/ifup.log & ;;
    esac
    rm /var/run/wlan.lock
fi

exit 0