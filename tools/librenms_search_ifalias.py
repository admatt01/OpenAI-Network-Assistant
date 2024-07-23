import requests
import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional

def librenms_search_ifalias(device_id: int) -> Dict[str, Any]:
    # Load environment variables
    load_dotenv()

    API_TOKEN = os.getenv('LIBRENMS_API_TOKEN')
    BASE_URL = os.getenv('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': API_TOKEN,
        'Content-Type': 'application/json'
    }

    url = f"{BASE_URL}/ports/search/device_id/{device_id}/"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while searching for the device: {str(e)}"}

# Example usage
if __name__ == "__main__":
    result = librenms_search_ifalias({"device_id": "11"})
    print(result)
    