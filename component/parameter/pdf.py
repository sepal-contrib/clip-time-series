from itertools import product


def get_dims(N):
    """
    I'm gonna check every combination from 1 to 20 lines and columns.
    400 year of data max, I'll have a good life before anyone complains.
    """
    # A4 format in landscape
    width = 11.69
    heigh = 8.27

    cols, lines = (None, None)
    li = 0
    for nb_col, nb_line in product(range(1, 21), range(1, 21)):

        l_tmp = min(width / nb_col, heigh / nb_line)

        if l_tmp > li and nb_col * nb_line > N:
            li = l_tmp
            cols = nb_col
            lines = nb_line

    return (cols, lines)


def getPositionPdf(i, nb_col):
    """Return the position of the square on the pdf page."""
    return [int(i / nb_col), i % nb_col]
