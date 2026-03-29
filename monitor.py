import psutil
import time
from googleapiclient import discovery
from google.oauth2 import service_account

# =========================
# CONFIGURATION
# =========================
THRESHOLD = 75
PROJECT = 'autoscaling-491618'       
ZONE = 'asia-south1-a'          
INSTANCE_NAME = 'auto-vm-instance'

# =========================
# CHECK USAGE
# =========================
def get_usage():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    usage = max(cpu, memory)
    print(f"CPU: {cpu}%, Memory: {memory}% → Using: {usage}%")
    return usage

# =========================
# CREATE GCP VM
# =========================
def trigger_cloud():
    print("\n🚀 Threshold exceeded! Launching GCP VM...\n")

    credentials = service_account.Credentials.from_service_account_file(
        'gcp-key.json'
    )

    compute = discovery.build('compute', 'v1', credentials=credentials)

    config = {
        'name': INSTANCE_NAME,

        'machineType': f'zones/{ZONE}/machineTypes/e2-micro',

        'disks': [{
            'boot': True,
            'autoDelete': True,
            'initializeParams': {
                'sourceImage': 'projects/debian-cloud/global/images/family/debian-11'
            }
        }],

        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [{
                'type': 'ONE_TO_ONE_NAT',
                'name': 'External NAT'
            }]
        }],

        # AUTO INSTALL APACHE (for demo)
        'metadata': {
            'items': [{
                'key': 'startup-script',
                'value': '''#!/bin/bash
                apt update
                apt install apache2 -y
                echo "Hello from GCP Auto-Scaled VM" > /var/www/html/index.html
                systemctl start apache2
                '''
            }]
        }
    }

    response = compute.instances().insert(
        project=PROJECT,
        zone=ZONE,
        body=config
    ).execute()

    print("GCP VM creation triggered!")
    print("Response:", response)

# =========================
# MAIN LOOP
# =========================
while True:
    usage = get_usage()

    if usage > THRESHOLD:
        trigger_cloud()
        break

    time.sleep(5)
