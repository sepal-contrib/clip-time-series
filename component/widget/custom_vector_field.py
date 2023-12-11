import geopandas as gpd
import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from traitlets import Dict


class CustomVectorField(v.Col, sw.SepalWidget):
    """
    A custom input widget to load vector data. The user will provide a vector file compatible with fiona.
    Then the user will select the comlumn to use as Id in the pdf.
    """

    v_model = Dict(
        {
            "pathname": None,
            "id_column": None,
        }
    ).tag(sync=True)

    def __init__(self):
        self.w_file = sw.FileInput(
            [".shp", ".geojson", ".gpkg", ".kml"], label="Select vector file"
        )

        self.w_column = v.Select(
            items=[],
            label="Id column",
            v_model=None,
        )

        super().__init__(children=[self.w_file, self.w_column])

        # events
        self.w_file.observe(self._update_file, "v_model")
        self.w_column.observe(self._update_column, "v_model")

    def reset(self):
        """
        Return the field to its initial state.

        Return:
            self
        """
        self.w_file.reset()

        return self

    @su.switch("loading", on_widgets=["w_column"])
    def _update_file(self, change):
        """update the file name, the v_model and reset the other widgets."""
        # reset the widgets
        self.w_column.items = []
        self.w_column.v_model = None

        # set the pathname value
        tmp = self.v_model.copy()
        tmp["pathname"] = change["new"]
        self.v_model = tmp

        # exit if nothing
        if not change["new"]:
            return self

        # read the file
        df = gpd.read_file(change["new"], ignore_geometry=True)
        columns = df.columns.to_list()

        # update the columns
        self.w_column.items = sorted(set(columns))

        return self

    def _update_column(self, change):
        """Update the column name and empty the value list."""
        # set the value
        tmp = self.v_model.copy()
        tmp["id_column"] = change["new"]
        self.v_model = tmp

        return self
