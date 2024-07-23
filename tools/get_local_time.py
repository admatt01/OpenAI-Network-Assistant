from datetime import datetime
from pytz import timezone, UnknownTimeZoneError
from typing import Dict, Any

def get_local_time(args: Dict[str, Any]) -> Dict[str, Any]:
    time_zone = args.get('timeZone', 'Australia/Sydney')

    try:
        tz = timezone(time_zone)
        local_time = datetime.now(tz)
        
        return {
            'local_time': local_time.strftime('%Y-%m-%d %H:%M:%S'),
            'time_zone': time_zone
        }
    except UnknownTimeZoneError:
        return {"error": f"Invalid time zone specified: {time_zone}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

# Example usage
if __name__ == "__main__":
    result = get_local_time({"timeZone": "Europe/London"})
    print(result)
