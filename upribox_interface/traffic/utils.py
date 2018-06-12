# coding: utf-8
import re
from .ntopng import Metric, device_day_stats
from lib.stats import get_week_days
from colour import Color


def get_protocol_sums(traffic):
    protocols = parse_traffic_dict(traffic)

    amounts = dict()
    texts = dict()

    for protocol in protocols.keys():
        text = list()
        amount = 0.0
        text.append(protocol.encode('utf-8'))
        if 'sent' in protocols[protocol] and float(protocols[protocol]['sent']) > 0:
            value = protocols[protocol]['sent']
            text.append('▲ {}'.format(value))
            amount += value
        if 'rcvd' in protocols[protocol] and float(protocols[protocol]['rcvd']) > 0:
            value = protocols[protocol]['rcvd']
            text.append('▼ {}'.format(value))
            amount += value
        amounts[protocol] = round(amount, 2)
        texts[protocol] = ' '.join(text)

    return amounts, texts


def parse_traffic_dict(traffic):
    result = dict()
    for datatype in traffic.keys():
        protocol, direction = re.match(r'^(.+)\ \((.+)\)$', datatype).group(1, 2)
        if protocol not in result:
            result[protocol] = dict()
        result[protocol][direction.lower()] = traffic[datatype]
    return result


def get_weekly_traffic(year, week, dev_ip):

    from collections import Counter
    total_protocols = Counter()
    days = []
    total = 0
    colors = list()

    for date in get_week_days(year, week):
        traffic = device_day_stats(date, dev_ip, sent_recv=True, metric=Metric.PROTOCOLS)
        traffic, texts = get_protocol_sums(traffic)
        #traffic = device_day_stats(date, dev.ip, metric=Metric.CATEGORIES)
        days.append({
            'date': date.strftime('%Y-%m-%d'),
            'traffic': traffic,
            'text': texts
        })

        total += sum(traffic.values())
        total_protocols.update(traffic)

    protocols_sorted = sorted(total_protocols, key=total_protocols.get, reverse=True)

    if len(protocols_sorted) > 0:
        colors = list(Color('#47ADC0').range_to(Color('black'), len(protocols_sorted)))

    return days, total, colors, texts, protocols_sorted


def get_protocols_by_volume(days, protocols_sorted, colors):

    protocols = list()

    for protocol in protocols_sorted:
        dates = list()
        amounts = list()
        texts = list()
        for day in days:
            dates.append(day['date'])
            if protocol in day['traffic']:
                amounts.append(day['traffic'][protocol])
                texts.append(day['text'][protocol])
            else:
                amounts.append(0.0)
                texts.append('-')
        protocols.append({'protocol': protocol, 'color': colors[protocols_sorted.index(protocol)].hex,
                          'dates': dates, 'amounts': amounts, 'texts': texts})
    protocols.reverse()

    return protocols
