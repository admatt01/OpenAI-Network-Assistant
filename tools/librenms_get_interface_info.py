import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

def librenms_get_interface_info(device_id: int, interface_name: str) -> Dict[str, Any]:
    # Load environment variables
    load_dotenv()

    API_TOKEN = os.getenv('LIBRENMS_API_TOKEN')
    BASE_URL = os.getenv('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': API_TOKEN,
        'Content-Type': 'application/json'
    }

    # Step 1: Search for the interface alias
    search_url = f"{BASE_URL}/ports/search/device_id/{device_id}/"
    try:
        search_response = requests.get(search_url, headers=headers)
        search_response.raise_for_status()
        search_result = search_response.json()
        
        # Find the port_id that matches the interface_name
        port_id = None
        for port in search_result.get('ports', []):
            # Normalize interface names for comparison
            if (port.get('ifName', '').lower().replace('/', '') == interface_name.lower().replace('/', '') or
                port.get('ifAlias', '').lower().replace('/', '') == interface_name.lower().replace('/', '')):
                port_id = port.get('port_id')
                break
        
        if port_id is None:
            return {"error": f"Interface {interface_name} not found on device {device_id}. Available interfaces: {[port['ifName'] + ' (' + port['ifAlias'] + ')' for port in search_result.get('ports', [])]}"}
        
        # Step 2: Retrieve port information
        port_url = f"{BASE_URL}/ports/{port_id}"
        port_response = requests.get(port_url, headers=headers)
        port_response.raise_for_status()
        port_info = port_response.json()
        
        # Add the matched interface name to the response for clarity
        port_info['matched_interface'] = interface_name
        
        return port_info

    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while fetching information: {str(e)}"}

# Example usage
if __name__ == "__main__":
    result = librenms_get_interface_info(device_id=3, interface_name="Ethernet0/0")
    print(result)