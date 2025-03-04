import os
import requests
import random
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcore.http.http_config import HttpConfig
from huaweicloudsdkcore.region.region import Region
from huaweicloudsdkdns.v2 import *
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
import time

# Set Huawei Cloud credentials
ak = os.environ["HUAWEI_ACCESS_KEY"]
sk = os.environ["HUAWEI_SECRET_KEY"]
project_id = os.environ["PROJECT_ID"]
zone_id = os.environ["ZONE_ID"]  # DNS Zone ID
domain_name = os.environ["DOMAIN_NAME"]  # Domain name to operate on

# Set the region (e.g., 'ap-southeast-1'), based on your situation
region = 'ap-southeast-1'

# Create client
credentials = BasicCredentials(ak, sk, project_id)
config = HttpConfig.get_default_config()

client = DnsClient.new_builder() \
    .with_credentials(credentials) \
    .with_region(Region(region, f"https://dns.{region}.myhuaweicloud.com")) \
    .with_http_config(config) \
    .build()

# Fetch IP addresses from the URL
try:
    response = requests.get('https://raw.githubusercontent.com/leung7963/CFIPS/main/ip.js')
    response.raise_for_status()
    ip_list = response.text.splitlines()
    print(f"Retrieved {len(ip_list)} IP addresses")
except requests.RequestException as e:
    print(f"Error fetching IP addresses: {str(e)}")
    ip_list = []

# Check if any IP addresses were retrieved
if not ip_list:
    print("No IP addresses found, exiting program.")
else:
    # Deduplicate IP addresses
    unique_ips = list(set(ip_list))
    print(f"Found {len(unique_ips)} unique IP addresses after deduplication.")
    
    # Randomly select up to 20 unique IPs
    selected_count = 20
    if len(unique_ips) < selected_count:
        selected_count = len(unique_ips)
        print(f"Note: Selecting {selected_count} IPs (all available unique IPs)")
    
    selected_ips = random.sample(unique_ips, selected_count)
    print(f"Randomly selected {len(selected_ips)} IPs for DNS update")

    # Delete existing 'A' records
    try:
        list_record_sets_request = ListRecordSetsRequest()
        list_record_sets_request.zone_id = zone_id
        record_sets = client.list_record_sets(list_record_sets_request).recordsets

        for record_set in record_sets:
            if record_set.type == "A" and record_set.name == domain_name + ".":
                delete_record_set_request = DeleteRecordSetRequest(
                    zone_id=zone_id,
                    recordset_id=record_set.id
                )
                try:
                    client.delete_record_set(delete_record_set_request)
                    print(f"Deleted old 'A' record: {record_set.name}")
                except exceptions.ClientRequestException as e:
                    if e.status_code == 404:
                        print(f"Record {record_set.name} not found, skipping.")
                    else:
                        print(f"Error deleting DNS record: {e.status_code} - {e.error_msg}")
                time.sleep(1)

    except exceptions.ClientRequestException as e:
        print(f"Error retrieving/deleting DNS records: {e.status_code} - {e.error_msg}")

    # Create new 'A' records with selected IPs
    try:
        for ip in selected_ips:
            create_record_set_request = CreateRecordSetWithLineRequest(
                zone_id=zone_id,
                body={
                    "name": domain_name + ".",
                    "type": "A",
                    "ttl": 86400,
                    "records": [ip],
                    "weight": "1"
                }
            )
            try:
                client.create_record_set_with_line(create_record_set_request)
                print(f"Created new 'A' record: {ip}")
            except exceptions.ClientRequestException as e:
                print(f"Error creating record: {e.status_code} - {e.error_msg}")
            time.sleep(1)
            
    except exceptions.ClientRequestException as e:
        print(f"Error creating DNS records: {e.status_code} - {e.error_msg}")