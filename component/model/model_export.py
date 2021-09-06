from traitlets import Any
from sepal_ui import model


class ExportModel(model.Model):

    vue = Any(None).tag(sync=True)
