import requests
import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional

def librenms_port_info(port_id: int) -> Dict[str, Any]:
    # Load environment variables
    load_dotenv()

    API_TOKEN = os.getenv('LIBRENMS_API_TOKEN')
    BASE_URL = os.getenv('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': API_TOKEN,
        'Content-Type': 'application/json'
    }

    url = f"{BASE_URL}/ports/{port_id}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while fetching port information: {str(e)}"}

# Example usage
if __name__ == "__main__":
    result = librenms_port_info(port_id=42)
    print(result)
    