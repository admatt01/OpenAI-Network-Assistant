import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def librenms_arp(query: str, device: str = None):
    """
    Retrieve ARP entries from LibreNMS.
    :param query: CIDR network (e.g., 10.0.0.0/24) or 'all' for all entries
    :param device: Device hostname or ID, required if query is 'all'
    :return: Dictionary containing the ARP entries and metadata
    """
    API_TOKEN = os.getenv('LIBRENMS_API_TOKEN')
    BASE_URL = os.getenv('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': API_TOKEN,
        'Content-Type': 'application/json'
    }

    try:
        if query == 'all' and device:
            response = requests.get(f"{BASE_URL}/resources/ip/arp/all", headers=headers, params={'device': device})
        else:
            response = requests.get(f"{BASE_URL}/resources/ip/arp/{query}", headers=headers)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve ARP entries: {str(e)}",
            "count": 0,
            "arp": []
        }
