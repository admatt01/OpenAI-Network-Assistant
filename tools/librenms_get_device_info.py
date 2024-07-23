import os
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def librenms_get_device_info(hostname: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves device information from LibreNMS. Can fetch details for all devices or a specific device using its hostname.
    """
    api_token = os.getenv('LIBRENMS_API_TOKEN')
    base_url = os.getenv('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': api_token,
        'Content-Type': 'application/json'
    }

    url = f"{base_url}/devices" if not hostname else f"{base_url}/devices/{hostname}"

    try:
        response = requests.get(url, headers=headers)
        
        # Print debug information
        print(f"Request URL: {response.url}")
        print(f"Request Headers: {headers}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text[:500]}...")  # Print first 500 characters of response
        
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        return response.json()

    except requests.RequestException as e:
        error_message = f"Error retrieving device information: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f"\nStatus code: {e.response.status_code}"
            error_message += f"\nResponse body: {e.response.text}"
        raise  # Re-raise the original exception

# Test the function
if __name__ == "__main__":
    try:
        result = librenms_get_device_info()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        