## 2024-05-20 - ReDoS vulnerability in location parsing
**Vulnerability:** A Regular Expression Denial of Service (ReDoS) vulnerability in `src/daylight_py/ipinfo.py` due to a badly crafted regex `re.match(r"^(-?\d+\.?\d*),(-?\d+\.?\d*)$", loc_str)`. The optional dot followed by `\d*` alongside the initial `\d+` creates catastrophic backtracking.
**Learning:** Using regex for parsing simple, delimited, structured strings (like "lat,lon") can easily introduce ReDoS vectors. The Python `str.split()` mechanism combined with type coercion is inherently immune to this.
**Prevention:** Avoid regex for parsing structured lists. Use native string splitting whenever possible. When regex is necessary, rigorously test for ReDoS vectors.

## 2024-05-20 - Unexpected interaction with astral v3.2 on polar days
**Vulnerability:** None (functional issue discovered during testing). The `get_sun_times` function misclassified summer solstice (polar day) at extreme latitudes (like Tromsø) as polar night.
**Learning:** In astral v3.2, `sun()` throws a ValueError if twilight/sunrise/sunset bounds are not crossed. Missing events don't strictly imply polar night.
**Prevention:** Always verify the actual sun elevation at solar noon if astral throws a ValueError to distinguish between polar day and polar night.
