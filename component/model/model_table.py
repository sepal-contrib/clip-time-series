from sepal_ui import model
from traitlets import Any

from component import parameter as cp


class TableModel(model.Model):

    # Input
    types = Any(cp.types[0]).tag(sync=True)
    json_table = Any(None).tag(sync=True)

    # Output
    raw_geometry = Any(None).tag(sync=True)
