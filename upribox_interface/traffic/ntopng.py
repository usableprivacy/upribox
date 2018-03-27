import datetime
from enum import Enum

import requests

from lib.utils import check_ip
from netaddr import IPAddress


class Metric(Enum):
    PROTOCOLS = 'allprotocols_bps'
    CATEGORIES = 'allcategories_bps'
    TRAFFIC_PACKETS_PER_SECOND = 'traffic_pps'
    TRAFFIC_BITS_PER_SECOND = 'traffic_bps'
    TOTAL_BYTES = 'traffic_total_bytes'
    TOTAL_PACKETS = 'traffic_total_packets'


QUERY_URL = "http://127.0.0.1:3000/lua/modules/grafana/upri.lua"

# QUERY_URL = "http://127.0.0.1:3000/lua/modules/grafana/query.lua"


# date: datetime.date object
def _device_day_data(date, host, metric):
    payload = {
        "range": {
            "from": "{}T00:00:00.000Z".format(date.strftime("%Y-%m-%d")),
            "to": "{}T23:59:59.999Z".format(date.strftime("%Y-%m-%d"))
        },
        "targets": [{
            "target": "host_{}_interface_view:eth0,wlan0_{}".format(host, metric.value)
        }],
        "maxDataPoints": 600  # requesting less points might result in scaling
    }

    r = requests.post(QUERY_URL, json=payload)
    r.raise_for_status()

    # resulting json has following format
    # [{"target": "SSH (Sent)  [192.168.76.129, view:eth0,wlan0]", "datapoints": [[0, 1516147500000], [], ...}, {}, ...]
    # [{"target": "Protocol (Direction)  [Host, Interface or View]", "datapoints": [[bits per seconds value, timestamp], [], ...}, {}, ...]
    return r.json()


def convert_to_megabytes(byte_count):
    return round((byte_count / (1024.0 * 1024.0)), 2)


# date(datetime.date object)
# host(str): ip address
# sent_recv(bool): separate sent and receveived values (only protocols)
# metric(Metric): ntopng supported metric
def device_day_stats(date, host, sent_recv=True, metric=Metric.PROTOCOLS):
    if not check_ip(host):
        raise ValueError("host is not a valid IP address")

    if metric not in Metric:
        raise ValueError("not a supported metric")

    res = {}
    byte = 8.0  # bits
    time_factor = 300 * 12  # seconds of one rrd interval (1 h) for intervals older than 24 hours
    if datetime.date.today() == date:
        time_factor = 300  # seconds of one rrd interval (5 min) for values of the last 24 hours

    data = _device_day_data(date, host, metric)

    for proto in data:
        if sent_recv and metric == Metric.PROTOCOLS:
            # separate values for sent and received of one protocol
            key = " ".join(proto['target'].split(" ")[:2])
        else:
            # sum up values for send and received of one protocol
            key = proto['target'].split(" ")[0]

        res.setdefault(key, 0)
        # calculates bytes from given bps values
        res[key] += sum((point[0] / byte) * time_factor for point in proto['datapoints'])

    final_result = {protocol: convert_to_megabytes(byte_count) for protocol, byte_count in res.items()}

    return final_result


def get_active_hosts(mode='local', api='grafana'):
    if mode not in ('local', 'remote', 'all'):
        raise ValueError("allowed modes: all, remote, local")
        return

    if api not in ('grafana', 'old'):
        raise ValueError("allowed apis: grafana, old")
        return
    elif api == 'grafana':
        return _get_grafana_hosts(mode)
    elif api == 'old':
        return _get_export_hosts(mode)


def _get_export_hosts(mode='local'):
    cookies = dict(user="nologin")
    r = requests.get("http://127.0.0.1:3000/lua/do_export_data.lua?ifid=2&mode={}&search=".format(mode), cookies=cookies)
    r.raise_for_status()
    return r.json()['hosts'].keys()


def _get_grafana_hosts(mode='local'):
    if mode == 'local':
        return _get_local_hosts()
    elif mode == 'remote':
        return _get_remote_hosts()
    elif mode == 'all':
        return _get_all_hosts()


def _get_all_hosts():
    # get all hosts: local, remote and multicasts
    r = requests.post("http://127.0.0.1:3000/lua/modules/grafana/search.lua")
    r.raise_for_status()

    return list({entry.split("_")[1] for entry in r.json()})


def _get_local_hosts():
    return _filter_hosts(lambda ip: ip.is_private() and ip.is_unicast())


def _get_remote_hosts():
    # to be complient with the ntopng term "remote", this will pretty much return anything that is not local (private class A,B or C network)
    # e.g. also multicasts like 239.255.255.250 and 224.0.0.1 will be returned
    return _filter_hosts(lambda ip: (not ip.is_private() or not ip.is_unicast()) and not ip.is_reserved())

    # this would only return real remote hosts
    # return _filter_hosts(lambda ip: not ip.is_private() and ip.is_unicast())


def _filter_hosts(condition):
    res = []
    for entry in _get_all_hosts():
        ip = IPAddress(entry)
        if condition(ip):
            res.append(entry)

    return res
