import requests
import pytz
import re

IPINFO_URL = "https://ipinfo.io/json?inc=ip,loc,timezone"

class IPInfoError(Exception):
    """Custom exception for IPInfo errors."""
    pass

def fetch_ip_info():
    """
    Fetches IP-based location information from ipinfo.io.

    Returns:
        A dictionary containing 'ip', 'latitude', 'longitude', and 'timezone' (a pytz.timezone object).

    Raises:
        IPInfoError: If there's an issue fetching or parsing the data.
    """
    try:
        response = requests.get(IPINFO_URL, timeout=5) # 5 second timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
    except requests.exceptions.RequestException as e:
        raise IPInfoError(f"Error fetching IP info from {IPINFO_URL}: {e}")

    try:
        data = response.json()
    except ValueError as e:
        raise IPInfoError(f"Error decoding JSON response from {IPINFO_URL}: {e}")

    ip = data.get("ip")
    loc_str = data.get("loc")
    tz_str = data.get("timezone")

    if not ip:
        raise IPInfoError("IPInfo response missing 'ip' field.")
    if not loc_str:
        raise IPInfoError("IPInfo response missing 'loc' (location) field.")
    if not tz_str:
        raise IPInfoError("IPInfo response missing 'timezone' field.")

    # Parse location string "lat,long" safely (avoid ReDoS)
    parts = loc_str.split(',')
    if len(parts) != 2:
        raise IPInfoError(f"IPInfo returned invalid location format: {loc_str}")

    try:
        latitude = float(parts[0].strip())
        longitude = float(parts[1].strip())
    except ValueError:
        raise IPInfoError(f"IPInfo returned invalid location format: {loc_str}")

    if not (-90 <= latitude <= 90):
        raise IPInfoError(f"IPInfo returned invalid latitude: {latitude}")
    if not (-180 <= longitude <= 180):
        raise IPInfoError(f"IPInfo returned invalid longitude: {longitude}")

    # Load timezone
    try:
        timezone = pytz.timezone(tz_str)
    except pytz.exceptions.UnknownTimeZoneError:
        raise IPInfoError(f"IPInfo returned unknown timezone: {tz_str}")

    return {
        "ip": ip,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
    }

if __name__ == '__main__':
    # Example usage:
    try:
        info = fetch_ip_info()
        print("Successfully fetched IP Info:")
        print(f"  IP Address: {info['ip']}")
        print(f"  Latitude: {info['latitude']}")
        print(f"  Longitude: {info['longitude']}")
        print(f"  Timezone: {info['timezone']}")
    except IPInfoError as e:
        print(f"Error: {e}")
