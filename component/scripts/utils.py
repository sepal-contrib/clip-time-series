from math import sqrt


def min_diagonal(polygon, square_size):
    """
    Return the min diameter of the smallest circle around the shape in 3857.

    Args:
        polygon (shapely geometry): the polygon in 3857
        square_size (int): the size of the desired buffer around the polygon
    """
    minx, miny, maxx, maxy = polygon.bounds

    # get the diagonal
    return max(square_size, sqrt((maxx - minx) ** 2 + (maxy - miny) ** 2))
