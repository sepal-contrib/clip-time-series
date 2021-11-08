from traitlets import Any

from sepal_ui import model
from component import parameter as cp


class VizModel(model.Model):

    # viz io is initialized with gee default data
    # (full landsat in rgb from 2008 to 2018)

    # inputs
    id_list = Any(["all"]).tag(sync=True)
    driver = Any(cp.drivers[0]).tag(sync=True)
    check = Any(False).tag(sync=True)
    bands = Any([*cp.getAvailableBands()][0]).tag(sync=True)
    mosaics = Any([]).tag(sync=True)  # years for GEE and mosaics name for planet
    image_size = Any(2000).tag(sync=True)  # in meters
    square_size = Any(30).tag(sync=True)  # in meters

    # gee related input
    sources = Any([]).tag(sync=True)

    # planet inputs
    planet_key = Any(None).tag(sync=True)

    # filtered point dataset
    pts = Any(None).tag(sync=True)
