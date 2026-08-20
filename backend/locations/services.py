from math import atan2, cos, radians, sin, sqrt


def calculate_distance(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
) -> float:
    """Calculate the great-circle distance between two coordinates in kilometers."""

    earth_radius = 6371.0

    lat1 = radians(float(from_latitude))
    lon1 = radians(float(from_longitude))
    lat2 = radians(float(to_latitude))
    lon2 = radians(float(to_longitude))

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c
