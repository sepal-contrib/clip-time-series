from traitlets import Any

from sepal_ui import model
from component import parameter as cp


class VizModel(model.Model):

    # viz io is initialized with gee default data
    # (full landsat in rgb from 2008 to 2018)

    # inputs
    driver = Any(cp.drivers[0]).tag(sync=True)
    check = Any(False).tag(sync=True)
    bands = Any([*cp.getAvailableBands()][0]).tag(sync=True)
    start_year = Any(2008).tag(sync=True)
    end_year = Any(2018).tag(sync=True)
    image_size = Any(2000).tag(sync=True)  # in meters
    square_size = Any(30).tag(sync=True)  # in meters

    # gee related input
    sources = Any([cp.sources[0]]).tag(sync=True)

    # planet inputs
    planet_key = Any(None).tag(sync=True)
    semester = Any(None).tag(sync=True)
