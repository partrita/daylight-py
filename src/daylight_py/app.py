import argparse
import datetime
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Displays sunrise, sunset, and daylight information."
    )

    parser.add_argument(
        "--latitude", type=float, help="Set latitude (requires --longitude)"
    )
    parser.add_argument(
        "--longitude", type=float, help="Set longitude (requires --latitude)"
    )
    parser.add_argument(
        "--timezone", type=str, help="Timezone in IANA format (e.g., 'Europe/London')"
    )
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format")
    parser.add_argument("--short", action="store_true", help="Show in condensed format")
    parser.add_argument("--json", action="store_true", help="Short JSON output")

    args = parser.parse_args()

    # Defer heavy imports until after argument parsing
    import pytz
    from .ipinfo import fetch_ip_info, IPInfoError
    from .calculations import get_sun_times
    from .json_view import create_json_output
    from .condensed_view import create_condensed_output
    from .full_view import create_full_output

    # Validation similar to the Go version's Config() method
    if (args.latitude is None) != (args.longitude is None):
        parser.error("--latitude and --longitude must both be set, if used")

    if args.latitude is not None and not (-90 <= args.latitude <= 90):
        parser.error("--latitude must be between -90 and 90")

    if args.longitude is not None and not (-180 <= args.longitude <= 180):
        parser.error("--longitude must be between -180 and 180")

    parsed_date = None
    if args.date:
        try:
            parsed_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            parser.error("--date was not a valid date in YYYY-MM-DD format")

    # Determine target date
    target_date = parsed_date if parsed_date else datetime.datetime.now().date()
    yesterday_date = target_date - datetime.timedelta(days=1)

    # Determine location and timezone
    latitude = args.latitude
    longitude = args.longitude
    timezone_pytz = None
    ip_address_val = None
    offline_mode = False

    if args.timezone:
        try:
            timezone_pytz = pytz.timezone(args.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            parser.error(f"Unknown timezone: {args.timezone}")

    if latitude is not None and longitude is not None and timezone_pytz is not None:
        offline_mode = True  # All required info provided
    elif latitude is not None and longitude is not None and timezone_pytz is None:
        # If lat/long are given but no TZ, this is an issue.
        # The Go app would fetch from IPInfo and then use provided lat/long if TZ was missing.
        # For simplicity, let's require TZ if lat/long are manually set for offline mode.
        # Or, alternatively, fetch IPInfo to get TZ and then override lat/long.
        # The original Go app seems to prioritize provided args, then fills with IPInfo.
        # Let's try to fetch IP info if timezone is missing, even if lat/long are present.
        pass  # Will fall through to IPInfo fetch if tz is still None

    if not offline_mode:
        try:
            print("Fetching IP information...", file=sys.stderr)
            ip_data = fetch_ip_info()
            ip_address_val = ip_data["ip"]
            if latitude is None:  # Prioritize CLI args for lat/long
                latitude = ip_data["latitude"]
            if longitude is None:
                longitude = ip_data["longitude"]
            if timezone_pytz is None:  # Prioritize CLI arg for TZ
                timezone_pytz = ip_data["timezone"] # Already a pytz timezone object
            print(
                f"Using: Lat={latitude:.2f}, Lon={longitude:.2f}, TZ={timezone_pytz.zone}",
                file=sys.stderr,
            )
        except IPInfoError as e:
            print(f"Error fetching IP information: {e}", file=sys.stderr)
            if latitude is None or longitude is None or timezone_pytz is None:
                print(
                    "Could not determine location. Please provide --latitude, --longitude, and --timezone, or ensure internet connectivity.",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                print(
                    "Proceeding with user-provided location data (if any).",
                    file=sys.stderr,
                )
                offline_mode = (
                    True  # Attempt to run offline if we have enough manual args
                )

    # Final check if we have all necessary info
    if latitude is None or longitude is None or timezone_pytz is None:
        print(
            "Error: Missing location information (latitude, longitude, or timezone).",
            file=sys.stderr,
        )
        print(
            "Please provide them as arguments or ensure IP-based lookup can succeed.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Apply the determined timezone to the date (making it aware for calculations if needed by astral, though date itself is naive)
    # The get_sun_times function expects a naive date object and a pytz timezone object.

    # Get sun times for today (or target_date) and yesterday
    try:
        sun_times_today = get_sun_times(latitude, longitude, target_date, timezone_pytz)
        sun_times_yesterday = get_sun_times(
            latitude, longitude, yesterday_date, timezone_pytz
        )
    except Exception as e:
        print(f"Error calculating sun times: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Output ---
    if args.json:
        ip_info_for_json = {"latitude": latitude, "longitude": longitude}
        if ip_address_val:
            ip_info_for_json["ip"] = ip_address_val

        print(
            create_json_output(
                target_date,
                sun_times_today,
                sun_times_yesterday,
                ip_address=ip_address_val,
                location={"latitude": latitude, "longitude": longitude},
            )
        )
    elif args.short:
        print(create_condensed_output(sun_times_today, sun_times_yesterday))
    else:  # Full output
        ten_day_projection_data = []
        for i in range(1, 11):
            proj_date = target_date + datetime.timedelta(days=i)
            try:
                proj_st = get_sun_times(latitude, longitude, proj_date, timezone_pytz)
                ten_day_projection_data.append((proj_date, proj_st))
            except Exception as e:
                print(
                    f"Warning: Could not calculate sun times for {proj_date}: {e}",
                    file=sys.stderr,
                )
                # Add a placeholder or skip? For now, skip.

        ip_info_for_full = None
        if ip_address_val:  # Only show IP if it was fetched
            ip_info_for_full = {
                "ip": ip_address_val,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone_pytz.zone,
            }
        elif offline_mode:  # Show location if offline but no IP
            ip_info_for_full = {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone_pytz.zone,
            }

        print(
            create_full_output(
                query_date=target_date,
                sun_times_today=sun_times_today,
                sun_times_yesterday=sun_times_yesterday,
                ten_day_projection=ten_day_projection_data,
                ip_info=ip_info_for_full,
                offline_mode=offline_mode
                and not ip_address_val,  # Truly offline if no IP was fetched
            )
        )


if __name__ == "__main__":
    # The sys.path manipulation below is usually for development/testing
    # when running app.py directly and the package isn't properly installed.
    # For `uv run` which uses entry points, it's often not strictly necessary,
    # but keeping it here doesn't hurt.
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    main()
