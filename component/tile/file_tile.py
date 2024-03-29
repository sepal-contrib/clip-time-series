import geopandas as gpd
import ipyvuetify as v
import pandas as pd
from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component import scripts as cs
from component import widget as cw
from component.message import cm


class TestTile(sw.Tile):
    def __init__(self, file_tile):
        # create the widgets
        txt = sw.Markdown(cm.table.test.txt)
        self.alert = sw.Alert()

        # get the file_tile to further use
        self.file_tile = file_tile

        # create the tile
        super().__init__(
            id_="file_widget",
            title=cm.table.test.title,
            alert=self.alert,
            btn=sw.Btn(
                cm.table.test.btn, icon="mdi-cloud-download", outlined=True, small=True
            ),
            inputs=[txt],
        )

        # js behaviour
        self.btn.on_event("click", self._import_test_file)

    @su.loading_button()
    def _import_test_file(self, widget, event, data):
        # download the test dataset to the download folder
        test_file = cs.download_test_file(self.alert)

        # add the file name to the file selector
        self.file_tile.table_select.fileInput.select_file(test_file)
        self.file_tile.w_file_type.v_model = cp.types[0]

        # trigger the validation
        self.file_tile.btn.fire_event("click", None)

        return


class FileTile(sw.Tile):
    def __init__(self, tb_model, m):
        # gather model
        self.model = tb_model

        # get the map
        self.m = m

        # filde selection type
        self.w_file_type = v.RadioGroup(
            label=cm.table.types,
            row=True,
            v_model=self.model.types,
            children=[v.Radio(key=i, label=n, value=n) for i, n in enumerate(cp.types)],
        )

        # create widgets
        self.vector_select = cw.CustomVectorField().hide()
        self.table_select = sw.LoadTableField()

        # bind it to the model
        (
            self.model.bind(self.vector_select, "json_table")
            .bind(self.table_select, "json_table")
            .bind(self.w_file_type, "types")
        )

        # create the tile
        super().__init__(
            id_="file_widget",
            title=cm.table.title,
            btn=sw.Btn(cm.table.btn),
            alert=sw.Alert(),
            inputs=[self.w_file_type, self.table_select, self.vector_select],
        )

        # js behaviour
        self.btn.on_event("click", self._load_file)
        self.w_file_type.observe(self._change_type, "v_model")
        self.vector_select.w_column.observe(self._test_unique, "v_model")
        self.table_select.IdSelect.observe(self._test_unique, "v_model")

    def _change_type(self, change):
        if change["new"] == cp.types[0]:  # table
            self.table_select.show()
            self.vector_select.hide()
        elif change["new"] == cp.types[1]:  # vector
            self.table_select.hide()
            self.vector_select.show()
        else:
            raise ValueError("This is not a recognized type")

        # empty the selectors
        self.table_select.reset()
        self.vector_select.reset()

        return self

    @su.loading_button()
    def _load_file(self, widget, event, data):
        # define variable
        table = self.model.json_table
        id_ = table["id_column"]
        file = table["pathname"]

        # check the variables
        if not all(
            [
                self.alert.check_input(file, cm.table.not_a_file),
                self.alert.check_input(id_, cm.table.missing_input),
            ]
        ):
            return

        if self.model.types == cp.types[0]:  # table
            lat = table["lat_column"]
            lng = table["lng_column"]

            # create the pts geodataframe
            df = pd.read_csv(file, sep=None, engine="python")
            df = df.filter(items=[lat, lng, id_])
            df = df.rename(columns={lat: "lat", lng: "lng", id_: "id"})
            gdf = gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df.lng, df.lat), crs="EPSG:4326"
            )

        elif self.model.types == cp.types[1]:  # vector
            gdf = gpd.read_file(file).to_crs(4326)
            gdf = gdf.filter([id_, "geometry"])
            gdf = gdf.rename(columns={id_: "id"})

        # set the dataframe in output
        self.model.raw_geometry = gdf

        # load the map
        cs.setMap(self.model, self.m)

        self.alert.add_msg(cm.table.valid_columns, "success")

        return

    def _test_unique(self, change):
        """
        Check that the chosen column for the id has only unique value
        if that's not the case empty the v_model and display error message.
        """
        # exit if no new value
        if not change["new"]:
            return

        # assign the widget to a variable for reading convinience
        widget = change["owner"]

        # reset the error message
        widget.error_messages = None
        widget.error = False

        # read the file as a pandas dataframe
        df = gpd.read_file(self.model.json_table["pathname"], ignore_geometry=True)

        # check the id column
        # empty it if it's wrong
        # display an error message
        if df[change["new"]].duplicated().sum():
            widget.error_messages = [cm.table.duplicated]
            widget.error = True
            widget.v_model = None

        return


class MapTile(sw.Tile):
    def __init__(self):
        # create the widgets
        self.map = sm.SepalMap([cp.basemap])

        super().__init__(id_="file_widget", title=cm.table.map.title, inputs=[self.map])
