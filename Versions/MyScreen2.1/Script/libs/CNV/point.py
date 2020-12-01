import functools
import math

def distance(point_a, point_b):
    """Returns the distance between two points."""
    x0, y0 = point_a
    x1, y1 = point_b
    return math.fabs(x0 - x1) + math.fabs(y0 - y1)

def nearest(point, all_points):
    """Returns the closest point in all_points from the first parameter."""
    distance_from_point = functools.partial(distance, point)
    return min(all_points, key=distance_from_point)
