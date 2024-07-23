import requests
import os
import json
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def librenms_syslog(
    hostname: Optional[str] = None,
    limit: Optional[int] = None,
    from_time: Optional[str] = None,
    to_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve syslog entries from LibreNMS for all devices or a specific device.
    :param hostname: Either the device's hostname or ID (optional)
    :param limit: The maximum number of results to return (optional). Returns maximum 50 results if not specified.
    :param from_time: The start date and time or the event ID to search from (optional)
    :param to_time: The end date and time or the event ID to search to (optional)
    :return: Dictionary containing the syslog entries and metadata
    """
    API_TOKEN = os.getenv('LIBRENMS_API_TOKEN')
    BASE_URL = os.getenv('LIBRENMS_BASE_URL')
    headers = {
        'X-Auth-Token': API_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Construct the URL based on whether hostname is provided
    url = f"{BASE_URL}/logs/syslog"
    if hostname:
        url += f"/{hostname}"

    # Prepare query parameters
    params = {}
    if limit is not None:
        params['limit'] = limit
    if from_time is not None:
        params['from'] = from_time
    if to_time is not None:
        params['to'] = to_time

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response body: {response.json()}")
        return response.json()
    except requests.RequestException as e:
        error_message = f"Failed to retrieve syslog entries: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "syslog": []
        }

# Test the function
if __name__ == "__main__":
    try:
        result = librenms_syslog()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        
pass

functions_info = {
    "name": "librenms_syslog",
    "description": "Retrieves syslog entries from LibreNMS for all devices or a specific device. Allows filtering based on time range and limiting the number of results.",
    "parameters": {
        "type": "object",
        "properties": {
            "hostname": {
                "type": "string",
                "description": "Either the device's hostname or ID (optional)"
            },
            "limit": {
                "type": "number",
                "description": "The maximum number of results to return (optional)"
            },
            "from_time": {
                "type": "string",
                "format": "date-time",
                "description": "The start date and time or the event ID to search from (optional)"
            },
            "to_time": {
                "type": "string",
                "format": "date-time",
                "description": "The end date and time or the event ID to search to (optional)"
            }
        }
    }
}
