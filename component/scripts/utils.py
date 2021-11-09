from math import sqrt


def min_diagonal(polygon, square_size):

    minx, miny, maxx, maxy = polygon.bounds

    # get the diagonal
    return max(square_size, sqrt((maxx - minx) ** 2 + (maxy - miny) ** 2))
