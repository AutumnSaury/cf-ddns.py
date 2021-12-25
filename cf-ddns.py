#!/usr/bin/env python3

import os
import re
import requests

# Your Cloudflare API key
apikey = 'ffffffffffffffffffffffffffffffff'
# E-Mail address of your Cloudflare account
mail_addr = 'username@example.com'
# TTL of your record, 1 for auto
ttl = 1
# Your domain
domain = 'example.com'
# Your subdomains under the domain above
subdomains = {'examplea', 'exampleb'}
# Cloudflare Zone ID of your domain
zone_id = 'ffffffffffffffffffffffffffffffff'
# Type of your record, A and AAAA supported
record_type = 'AAAA'
# The following 2 options will be used only when "record_type" is set to "AAAA"
# Name of your network card
net_dev = 'eth0'
# The last 64 bits of your IPv6 Address, usually determined by the MAC address of your network card
ipv6_suffix = 'ffff:ffff:ffff:ffff'
# An HTTP API which returns your public IPv4 address, content type of its response should be plain text, used only when "record_type" is set to "A"
ipv4_api = 'https://ipv4.icanhazip.com/'


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
    ).json()
    record_id = record['result'][0]['id']
    record_content = record['result'][0]['content']

    if record_content == ip_addr:
        return 600
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


def get_ip_addr(record_type: str, net_dev: str = 'eth0', api: str = 'https://ipv4.icanhazip.com/', suffix: str = 'ffff:ffff:ffff:ffff'):
    if record_type == 'AAAA':
        out = os.popen('ip -6 addr show dynamic dev ' + net_dev)
        result = out.readlines()
        result.pop(0)
        flag = False
        skip = False
        active_ips = []
        for line in result:
            flag = not flag
            if flag:
                address = re.search(
                    '(?<=inet6 ).*' + suffix + '(?=\/[0-9]{1,3} )',
                    line
                )
                if address:
                    active_ips.append({'address': address[0]})
                else:
                    skip = True
                    continue
            else:
                if skip:
                    skip = False
                    continue
                else:
                    active_ips[-1]['preferred_lft'] = int(
                        re.search('(?<=preferred_lft )[0-9]*(?=sec)', line)[0]
                    )
        out.close()
        active_ips.sort(key=lambda ip: ip['preferred_lft'])
        return active_ips[-1]['address']
    elif record_type == 'A':
        return re.search(
            r'([0-9]{1,3}\.?){4}',
            requests.get(api).text
        )[0]
    else:
        raise Exception('Unsupported record type')


ip_addr = get_ip_addr(
    record_type=record_type,
    net_dev=net_dev,
    api=ipv4_api,
    suffix=ipv6_suffix
)

for name in subdomains:
    status = update(
        apikey,
        mail_addr,
        name + '.' + domain,
        zone_id,
        ttl,
        ip_addr,
        record_type
    )
    if status == 200:
        continue
    elif status == 600:
        print("IP address wasn't changed, exiting.")
        exit(0)
    else:
        print(
            'An error occoured while updating the record of "' + name + '.' + domain + '"\n' +
            'Status code: ' + str(status)
        )
        exit(1)
print(
    'All records are now up to date.\n' +
    'New IP address: ' + ip_addr
)
exit(0)
