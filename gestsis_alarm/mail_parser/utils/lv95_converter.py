
def convert_lv95_to_wgs84(lv95_coordinate: str):
    """
    Convert CH1903+ (LV95/MN95) coordinates to WGS84.
    Precision: 0.1" (~2m)

    :param
        lv95_coordinate: str
          LV95 Coordinate in format "E,N".
    :return A tuple containing the WGS84 coordinate, First item is East, Second item is North.
        If the coordinate given are invalid, None if returned
    """
    coord = lv95_coordinate.split(",")
    if len(coord) != 2:
        return None

    east, north = float(coord[0]), float(coord[1])

    # This section follows the official recommendation for converting LV95 to WGS84 given by the Swiss Confederation
    # https://www.swisstopo.admin.ch/en/knowledge-facts/surveying-geodesy/reference-frames/local/lv95.html

    y = (east - 2600000) / 1000000
    x = (north - 1200000) / 1000000

    y2 = y ** 2
    y3 = y ** 3

    x2 = x ** 2
    x3 = x ** 3

    l = 2.6779094 \
        + 4.728982 * y \
        + (0.791484 * y * x) \
        + (0.1306 * y * x2) \
        - (0.0436 * y3)

    phi = 16.9023892 \
          + (3.238272 * x) \
          - (0.270978 * y2) \
          - (0.002528 * x2) \
          - (0.0447 * y2 * x) \
          - (0.0140 * x3)

    return l * 100 / 36, phi * 100 / 36
