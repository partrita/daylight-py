import unittest
from unittest.mock import patch, MagicMock
import pytz

# Add project root to sys.path to allow importing daylight_py
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from daylight_py.ipinfo import fetch_ip_info, IPInfoError

class TestIPInfo(unittest.TestCase):

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ip": "1.2.3.4",
            "loc": "51.50,-0.12", # Latitude, Longitude
            "timezone": "Europe/London"
        }
        mock_response.raise_for_status.return_value = None # Simulate successful HTTP status
        mock_get.return_value = mock_response

        info = fetch_ip_info()

        self.assertEqual(info["ip"], "1.2.3.4")
        self.assertAlmostEqual(info["latitude"], 51.50)
        self.assertAlmostEqual(info["longitude"], -0.12)
        self.assertEqual(info["timezone"], pytz.timezone("Europe/London"))
        mock_get.assert_called_once_with("https://ipinfo.io/json?inc=ip,loc,timezone", timeout=5)

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Test HTTP Error")
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "Error fetching IP info.*Test HTTP Error"):
            fetch_ip_info()

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_missing_loc(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ip": "1.2.3.4",
            # "loc": "51.50,-0.12", # Missing
            "timezone": "Europe/London"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "IPInfo response missing 'loc'"):
            fetch_ip_info()

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_invalid_loc_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ip": "1.2.3.4",
            "loc": "invalid_format",
            "timezone": "Europe/London"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "IPInfo returned invalid location format: invalid_format"):
            fetch_ip_info()

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_invalid_latitude_value(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ip": "1.2.3.4",
            "loc": "95.0,0.0", # Invalid latitude
            "timezone": "Europe/London"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "IPInfo returned invalid latitude: 95.0"):
            fetch_ip_info()

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_unknown_timezone(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ip": "1.2.3.4",
            "loc": "51.50,-0.12",
            "timezone": "Invalid/Timezone"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "IPInfo returned unknown timezone: Invalid/Timezone"):
            fetch_ip_info()

    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_json_decode_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("JSON Decode Error") # Simulate json.loads error
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "Error decoding JSON response.*JSON Decode Error"):
            fetch_ip_info()


    @patch('daylight_py.ipinfo.requests.get')
    def test_fetch_ip_info_invalid_ip(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ip": "[31mMALICIOUS IP[0m",
            "loc": "51.50,-0.12",
            "timezone": "Europe/London"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(IPInfoError, "IPInfo returned invalid IP address"):
            fetch_ip_info()

# This is needed to import requests for the side_effect
import requests

if __name__ == '__main__':
    unittest.main()
