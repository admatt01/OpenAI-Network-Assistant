import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API configuration
API_TOKEN = os.environ.get('LIBRENMS_API_TOKEN')
BASE_URL = os.environ.get('LIBRENMS_BASE_URL')

def librenms_bgp(
    hostname: Optional[str] = None,
    asn: Optional[str] = None,
    remote_asn: Optional[str] = None,
    bgp_adminstate: Optional[str] = None,
    bgp_family: Optional[str] = None,
    bgp_desc: Optional[str] = None,
    bgp_state: Optional[str] = None,
    local_address: Optional[str] = None,
    remote_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves BGP information from LibreNMS including detailed peering information, status and descriptions.
    """
    api_token = os.environ.get('LIBRENMS_API_TOKEN')
    base_url = os.environ.get('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': api_token,
        'Content-Type': 'application/json'
    }
    
    params = {
        k: v for k, v in locals().items() 
        if k in ['hostname', 'asn', 'remote_asn', 'bgp_adminstate', 'bgp_family', 
                 'bgp_desc', 'bgp_state', 'local_address', 'remote_address'] and v is not None
    }

    try:
        response = requests.get(f"{BASE_URL}/bgp", headers=headers, params=params)
        
        # Print debug information
        print(f"Request URL: {response.url}")
        print(f"Request Headers: {headers}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text[:500]}...")  # Print first 500 characters of response
        
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        return response.json()
    
    except requests.RequestException as e:
        error_message = f"Failed to retrieve BGP sessions: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f"\nStatus code: {e.response.status_code}"
            error_message += f"\nResponse body: {e.response.text}"
        raise  # Re-raise the original exception instead of ValueError

# Test the function
if __name__ == "__main__":
    try:
        result = librenms_bgp()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        