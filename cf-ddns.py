#!/usr/bin/env python3

import os
import re
import requests
import json

apikey = ''
mail_addr = ''
record_type = ''
ttl = 1
subdomains = {}
domain = ''
zone_id = ''
net_device = ''
ipv6_suffix = ''


def update(apikey: str, mail: str, url: str, zone_id: str, ttl: int, ip_addr: str, record_type: str):
    headers = {
        'X-Auth-Email': mail,
        'X-Auth-Key': apikey,
        'Content-Type': 'application/json'
    }
    record = requests.get(
        'https://api.cloudflare.com/client/v4/zones/' + zone_id + '/dns_records',
        headers=headers,
        params={'name': url}
    )
    record_id = record.json()['result'][0]['id']

    status = requests.put(
        'https://api.cloudflare.com/client/v4/zones/' +
        zone_id + '/dns_records/' + record_id,
        headers=headers,
        json={
            'id': zone_id,
            'type': record_type,
            'name': url,
            'content': ip_addr,
            'ttl': ttl
        }

    )
    return status.status_code


result = os.popen('ip -6 addr show dynamic dev ' + net_device).readlines()
result.pop(0)
flag = False
skip = False
activeIPs = []

for line in result:
    flag = not flag
    if flag:
        activeIPs.append({})
        address = re.search('(?<=inet6 ).*' + ipv6_suffix +
                            '(?=\/[0-9]{1,3} )', line)
        if address:
            activeIPs[-1]['address'] = address[0]
        else:
            skip = True
            activeIPs.pop(-1)
            continue
    else:
        if skip:
            skip = False
            continue
        else:
            activeIPs[-1]['preferred_lft'] = int(
                re.search('(?<=preferred_lft )[0-9]*(?=sec)', line)[0]
            )

activeIPs.sort(key=lambda ip: ip['preferred_lft'], reverse=True)

for name in subdomains:
    status = update(
        apikey,
        mail_addr,
        name + '.' + domain,
        zone_id,
        ttl,
        activeIPs[0]['address'],
        record_type
    )
    if status != 200:
        print('An error occoured while updating the record of "' +
              name + '.' + domain + '"')
        exit(1)
print('All records are now up to date.')
