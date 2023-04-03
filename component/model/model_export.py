from sepal_ui import model
from traitlets import Any


class ExportModel(model.Model):

    vue = Any(None).tag(sync=True)
