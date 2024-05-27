from sepal_ui import model
from traitlets import Any, Bool, Unicode


class ExportModel(model.Model):

    vue = Any(None).tag(sync=True)
    overwrite = Bool(True).tag(sync=True)
    enhance_method = Unicode("min_max").tag(sync=True)
