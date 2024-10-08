import os
import requests
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcore.http.http_config import HttpConfig
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
    .with_region(DnsRegion.value_of(region)) \
    .with_http_config(config) \
    .build()

# Fetch IP addresses from the URL
try:
    response = requests.get('https://raw.githubusercontent.com/leung7963/CFIPS/main/ip.txt')
    response.raise_for_status()
    ip_list = response.text.splitlines()
    print(f"Retrieved IP addresses: {ip_list}")
except requests.RequestException as e:
    print(f"Error fetching IP addresses: {str(e)}")
    ip_list = []

# Check if any IP addresses were retrieved
if not ip_list:
    #print("No IP addresses found, exiting program.")
#else:
    # Batch delete records
    try:
        list_record_sets_request = ListRecordSetsRequest()
        list_record_sets_request.zone_id = zone_id
        record_sets = client.list_record_sets(list_record_sets_request).recordsets

        # Collect all record IDs for deletion
        recordset_ids = [record_set.id for record_set in record_sets]

        if recordset_ids:
            batch_delete_request = BatchDeleteRecordSetWithLineRequest()
            batch_delete_request.body = BatchDeleteRecordSetWithLineRequestBody(
                recordset_ids=recordset_ids
            )

            try:
                response = client.batch_delete_record_set_with_line(batch_delete_request)
                print(f"Successfully deleted records: {recordset_ids}")
            except exceptions.ClientRequestException as e:
                print(f"Error during batch deletion: {e.status_code} - {e.error_msg}")
        else:
            print("No records found to delete.")

    except exceptions.ClientRequestException as e:
        print(f"Error retrieving DNS records: {e.status_code} - {e.error_msg}")

    # Create new 'A' DNS records
    try:
        for ip in ip_list:
            create_record_set_request = CreateRecordSetWithLineRequest(
                zone_id=zone_id,
                body={
                    "name": domain_name + ".",
                    "type": "A",
                    "ttl": 300,
                    "records": [ip],
                    "weight": "1"
                }
            )
            try:
                response = client.create_record_set_with_line(create_record_set_request)
                print(f"Created new 'A' record: {ip}")
            except exceptions.ClientRequestException as e:
                print(f"Error creating DNS record: {e.status_code} - {e.error_msg}")
            # Delay to avoid concurrency issues
            time.sleep(1)

    except exceptions.ClientRequestException as e:
        print(f"Error creating DNS records: {e.status_code} - {e.error_msg}")