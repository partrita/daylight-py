## 2024-05-18 - Missing IP Validation from External API
**Vulnerability:** The application was fetching IP and location data from `ipinfo.io` but blindly trusting the `ip` field in the JSON response without validating that it was actually a properly formatted IP address. This could potentially be used for spoofing or introducing unexpected data.
**Learning:** We cannot implicitly trust data returned from external APIs, even common ones, especially when that data is subsequently used in output, logging, or internal logic.
**Prevention:** Always use appropriate validators (e.g., `ipaddress.ip_address` in Python) to sanitize and verify fields returned from external HTTP requests before processing them.
