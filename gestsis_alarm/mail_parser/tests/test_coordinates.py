from unittest import TestCase
from ..utils.lv95_converter import convert_lv95_to_wgs84


class TestLV95Converter(TestCase):
    delta = 0.000025

    def test_invalid_string(self):
        """Test string containing no coordinate at all"""
        self.assertIsNone(convert_lv95_to_wgs84("FEU BAT ROUGE"))
        self.assertIsNone(convert_lv95_to_wgs84("4321123"))
        self.assertIsNone(convert_lv95_to_wgs84("FEU,BAT"))

    def test_textbook_example(self):
        """Perform the conversion given as an example in the manual"""
        # https://www.swisstopo.admin.ch/en/knowledge-facts/surveying-geodesy/reference-frames/local/lv95.html

        long, lat = convert_lv95_to_wgs84("2700000,1100000")
        # The delta represent an accuracy of about 2.5 meter : https://gis.stackexchange.com/a/8674
        # This has be chosen to be in accordance of the accuracy of the converter
        self.assertAlmostEqual(long, 8.730497, delta=self.delta)
        self.assertAlmostEqual(lat, 46.044131, delta=self.delta)

    def test_outside_coordinates(self):
        """Check if the converter detect coordinates outside of Switzerland"""
        self.assertIsNone(convert_lv95_to_wgs84("0,0"))
        self.assertIsNone(convert_lv95_to_wgs84("1000000,1000000"))
        self.assertIsNone(convert_lv95_to_wgs84("2593067.2, 1310000"))
        self.assertIsNone(convert_lv95_to_wgs84("2840001, 1199771.7"))

    def test_ju_coordinates(self):
        """Perform LV95 to WGS84 conversion for the capital of each of the three district in the canton of Jura"""

        # All the WGS84 coordinates have been obtained using the REFRAME service from the Swiss Confederation
        # It can convert coordinates with a precision of 2-3cm.
        # https://www.swisstopo.admin.ch/en/maps-data-online/calculation-services/m2m.html

        # Delémont
        long, lat = convert_lv95_to_wgs84("2593067.2, 1246045.6")
        self.assertAlmostEqual(long, 7.346847, delta=self.delta)
        self.assertAlmostEqual(lat, 47.365215, delta=self.delta)

        # Porrentruy
        long, lat = convert_lv95_to_wgs84("2572770.5, 1251864.9")
        self.assertAlmostEqual(long, 7.077801, delta=self.delta)
        self.assertAlmostEqual(lat, 47.417026, delta=self.delta)

        # Saignelégier
        long, lat = convert_lv95_to_wgs84("2566607.6, 1233954.6")
        self.assertAlmostEqual(long, 6.997475, delta=self.delta)
        self.assertAlmostEqual(lat, 47.255652, delta=self.delta)

    def test_extreme_points_coordinates(self):
        """Perform LV95 to WGS84 conversion for the extreme points of Switzerland and Bern"""

        # Northernmost point
        long, lat = convert_lv95_to_wgs84("2684601.4, 1295933.7")
        self.assertAlmostEqual(long, 8.568028, delta=self.delta)
        self.assertAlmostEqual(lat, 47.808454, delta=self.delta)

        # Southernmost point
        long, lat = convert_lv95_to_wgs84("2722706.6, 1075268.4")
        self.assertAlmostEqual(long, 9.017331, delta=self.delta)
        self.assertAlmostEqual(lat, 45.817960, delta=self.delta)

        # Westernmost  point
        long, lat = convert_lv95_to_wgs84("2485410.6, 1110070")
        self.assertAlmostEqual(long, 5.955907, delta=self.delta)
        self.assertAlmostEqual(lat,	46.132356, delta=self.delta)

        # Easternmost  point
        long, lat = convert_lv95_to_wgs84("2833857.5, 1166962.3")
        self.assertAlmostEqual(long, 10.492168, delta=self.delta)
        self.assertAlmostEqual(lat,  46.612955, delta=self.delta)

        # Bern
        long, lat = convert_lv95_to_wgs84("2599879.5, 1199771.7")
        self.assertAlmostEqual(long, 7.437050, delta=self.delta)
        self.assertAlmostEqual(lat, 46.949030, delta=self.delta)
