import datetime
from astral import LocationInfo
from astral.sun import noon, sunrise, sunset, elevation
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

    sunrise_utc = None
    sunset_utc = None
    noon_utc = None
    polar_day = False
    polar_night = False

    # 1. Always try to get solar noon
    try:
        noon_utc = noon(city.observer, date=date_obj, tzinfo=pytz.utc)
    except ValueError:
        # In extreme cases even noon might not be calculable?
        # But for Earthly latitudes it should be.
        pass

    # 2. Try to get sunrise/sunset
    try:
        sunrise_utc = sunrise(city.observer, date=date_obj, tzinfo=pytz.utc)
        sunset_utc = sunset(city.observer, date=date_obj, tzinfo=pytz.utc)
    except ValueError:
        # Polar condition: Sun is either always above or always below the horizon.
        if noon_utc:
            # Check elevation at noon to distinguish polar day from polar night.
            # Elevation > 0 means the sun is above the horizon at its highest point.
            if elevation(city.observer, noon_utc) > 0:
                polar_day = True
            else:
                polar_night = True
        else:
            # Fallback for very extreme cases (e.g. near poles where noon might fail)
            # Use latitude and month as a very rough fallback if needed,
            # but usually noon() works if latitude is within [-90, 90].
            if latitude > 0:
                # Northern Hemisphere: Summer (Apr-Sep) is likely polar day
                polar_day = 3 <= date_obj.month <= 9
                polar_night = not polar_day
            else:
                # Southern Hemisphere: Summer (Oct-Mar) is likely polar day
                polar_day = date_obj.month >= 10 or date_obj.month <= 3
                polar_night = not polar_day

    # Initialize return values
    rises_local = None
    sets_local = None
    noon_local = None
    length_td = None

    if polar_day:
        length_td = datetime.timedelta(days=1)
        noon_local = noon_utc.astimezone(timezone_pytz) if noon_utc else timezone_pytz.localize(datetime.datetime.combine(date_obj, datetime.time(12,0,0)))
    elif polar_night:
        length_td = datetime.timedelta(0)
    else:
        if sunrise_utc:
            rises_local = sunrise_utc.astimezone(timezone_pytz)
        if sunset_utc:
            sets_local = sunset_utc.astimezone(timezone_pytz)
        if noon_utc:
            noon_local = noon_utc.astimezone(timezone_pytz)
        
        if sunrise_utc and sunset_utc:
            length_td = sunset_utc - sunrise_utc

    return SunTimes(
        rises=rises_local,
        sets=sets_local,
        noon=noon_local,
        length=length_td,
        polar_day=polar_day,
        polar_night=polar_night,
        timezone=timezone_pytz
    )
