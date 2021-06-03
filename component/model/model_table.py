from traitlets import Any
from sepal_ui import model

class TableModel(model.Model):
    
    # Input
    json_table = Any(None).tag(sync=True)
    
    # Output
    pts = Any(None).tag(sync=True)