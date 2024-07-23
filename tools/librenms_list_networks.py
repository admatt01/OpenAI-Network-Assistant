import requests
import os
import json
from dotenv import load_dotenv
from typing import Dict, Any

def librenms_list_networks() -> Dict[str, Any]:
    # Load environment variables
    load_dotenv()

    API_TOKEN = os.getenv('LIBRENMS_API_TOKEN')
    BASE_URL = os.getenv('LIBRENMS_BASE_URL')

    headers = {
        'X-Auth-Token': API_TOKEN,
        'Content-Type': 'application/json'
    }

    url = f"{BASE_URL}/resources/ip/networks"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        data = response.json()
        
        # Return the whole response as the API doesn't have a specific 'networks' key
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while fetching network data: {str(e)}"}

# Example usage
if __name__ == "__main__":
    result = librenms_list_networks({})
    print(result)
