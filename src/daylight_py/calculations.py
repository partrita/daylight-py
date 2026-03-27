import datetime
from astral import LocationInfo
from astral.sun import sun # SunIsNotVisibleError is not directly exposed in v3 as such for sun()
import pytz

class SunTimes:
    def __init__(self, rises, sets, noon, length, polar_night=False, polar_day=False, timezone=pytz.utc):
        self.rises = rises
        self.sets = sets
        self.noon = noon
        self.length = length
        self.polar_night = polar_night
        self.polar_day = polar_day
        self.timezone = timezone # Store timezone for consistent output

    def __repr__(self):
        return (f"SunTimes(rises={self.rises}, sets={self.sets}, noon={self.noon}, length={self.length}, "
                f"polar_night={self.polar_night}, polar_day={self.polar_day}, timezone={self.timezone})")

def get_sun_times(latitude, longitude, date_obj, timezone_pytz):
    """
    Calculates sunrise, sunset, solar noon, and day length for a given location and date.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        date_obj (datetime.date): The date for which to calculate sun times.
        timezone_pytz (pytz.timezone): The timezone for the location.

    Returns:
        SunTimes: An object containing sunrise, sunset, noon, day length, and polar day/night status.
                  Times are timezone-aware (UTC by default from astral, then localized).
    """
    city = LocationInfo(timezone=timezone_pytz.zone, latitude=latitude, longitude=longitude)

    s = {} # Initialize in case sun() fails to return anything
    try:
        # Get sun events. Astral's sun() function returns a dictionary.
        # If an event like sunrise/sunset does not occur for the entire day,
        # its key might be absent from the dictionary.
        s = sun(city.observer, date=date_obj, tzinfo=pytz.utc)
    except ValueError:
        # A ValueError from sun() typically indicates that no sun events (not even twilight)
        # occurred for the entire day, signifying a clear polar day or polar night.
        pass # `s` will remain an empty dictionary, which our logic below handles.

    # Extract sun times from the dictionary; use .get() to safely handle missing keys
    sunrise_utc = s.get("sunrise")
    sunset_utc = s.get("sunset")
    noon_utc = s.get("noon")

    # Initialize flags for polar conditions
    polar_day = False
    polar_night = False
    
    # Initialize return values
    rises_local = None
    sets_local = None
    noon_local = None
    length_td = None

    # Determine polar day/night status based on the presence of sunrise and sunset
    if sunrise_utc is None and sunset_utc is None:
        # If both sunrise and sunset are absent, it's a polar condition.
        # We can distinguish between polar day and polar night by checking the sun's elevation.
        # If astral didn't return a noon time, approximate it to local 12:00 PM.
        from astral.sun import elevation
        test_noon = noon_utc if noon_utc else timezone_pytz.localize(datetime.datetime.combine(date_obj, datetime.time(12, 0, 0)))
        sun_elev = elevation(city.observer, test_noon)
        if sun_elev > 0:
            polar_day = True
        else:
            polar_night = True

    if polar_day:
        # For polar day, the sun is up for 24 hours.
        length_td = datetime.timedelta(days=1) # 24 hours
        # Sunrise and sunset are non-existent.
        rises_local = None
        sets_local = None
        # Solar noon is still a valid concept (the sun's highest point)
        # If astral provided it, localize it. Otherwise, approximate local midday.
        noon_local = noon_utc.astimezone(timezone_pytz) if noon_utc else timezone_pytz.localize(datetime.datetime.combine(date_obj, datetime.time(12,0,0)))
    elif polar_night:
        # For polar night, the sun is down for 24 hours.
        length_td = datetime.timedelta(0) # 0 hours
        # Sunrise, sunset, and solar noon are non-existent.
        rises_local = None
        sets_local = None
        noon_local = None
    else:
        # Normal day: Both sunrise and sunset occurred.
        # Localize the UTC times to the target timezone.
        if sunrise_utc:
            rises_local = sunrise_utc.astimezone(timezone_pytz)
        if sunset_utc:
            sets_local = sunset_utc.astimezone(timezone_pytz)
        if noon_utc:
            noon_local = noon_utc.astimezone(timezone_pytz)
        
        # Calculate day length from the UTC sunrise and sunset for accuracy.
        if sunrise_utc and sunset_utc:
            length_td = sunset_utc - sunrise_utc

    # Return a SunTimes object with all calculated/determined values.
    return SunTimes(
        rises=rises_local,
        sets=sets_local,
        noon=noon_local,
        length=length_td,
        polar_day=polar_day,
        polar_night=polar_night,
        timezone=timezone_pytz
    )