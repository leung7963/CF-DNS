import os
import requests
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcore.http.http_config import HttpConfig
from huaweicloudsdkcore.region.region import Region
from huaweicloudsdkdns.v2 import *
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion

# Set Huawei Cloud credentials
ak = os.environ["HUAWEI_ACCESS_KEY"]
sk = os.environ["HUAWEI_SECRET_KEY"]
project_id = os.environ["PROJECT_ID"]
zone_id = os.environ["ZONE_ID"]  # DNS Zone ID
domain_name = os.environ["DOMAIN_NAME"]  # Your domain name

# Set the region, e.g., 'ap-southeast-1'
region = 'ap-southeast-1'

# Create client
credentials = BasicCredentials(ak, sk, project_id)
config = HttpConfig.get_default_config()

client = DnsClient.new_builder() \
    .with_credentials(credentials) \
    .with_region(Region(region, f"https://dns.{region}.myhuaweicloud.com")) \
    .with_http_config(config) \
    .build()

# Fetch IP addresses from URL
try:
    response = requests.get('https://raw.githubusercontent.com/leung7963/CFIPS/main/ip.txt')
    ip_list = response.text.splitlines()
    print(f"IP addresses fetched: {ip_list}")
except requests.RequestException as e:
    print(f"Error fetching IP addresses: {str(e)}")
    ip_list = []

# Check if IP addresses were retrieved
if not ip_list:
    print("No IP addresses retrieved. Exiting.")
else:
    # Delete all A records
    try:
        list_record_sets_request = ListRecordSetsRequest()
        list_record_sets_request.zone_id = zone_id
        record_sets = client.list_record_sets(list_record_sets_request).recordsets

        for record_set in record_sets:
            if record_set.type == "A":
                delete_record_set_request = DeleteRecordSetRequest(
                    zone_id=zone_id, 
                    recordset_id=record_set.id
                )
                client.delete_record_set(delete_record_set_request)
                print(f"Deleted A record: {record_set.name}")
    except exceptions.ClientRequestException as e:
        print(f"Error deleting DNS records: {e.status_code} - {e.error_msg}")

    # Create new DNS A records
    try:
        for ip in ip_list:
            create_record_set_request = CreateRecordSetWithLineRequest(
                zone_id=zone_id,
                body={
                    "name": domain_name + ".",
                    "type": "A",
                    "ttl": 1,
                    "records": [ip],
                    "weight": "1"
                }
            )
            response = client.create_record_set_with_line(create_record_set_request)
            print(f"Created new DNS A record: {ip}")
    except exceptions.ClientRequestException as e:
        print(f"Error creating DNS records: {e.status_code} - {e.error_msg}")
