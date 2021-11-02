import json

import pandas as pd
import geopandas as gdp
import ipyvuetify as v

from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from sepal_ui.scripts import utils as su

from component import scripts as cs
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
            btn=sw.Btn(cm.table.test.btn, outlined=True, small=True),
            inputs=[txt],
        )

        # js behaviour
        self.btn.on_event("click", self._import_test_file)

    @su.loading_button(debug=True)
    def _import_test_file(self, widget, event, data):

        # download the test dataset to the download folder
        test_file = cs.download_test_file(self.alert)

        # add the file name to the file selector
        self.file_tile.file_select.fileInput.select_file(test_file)

        # trigger the validation
        self.file_tile.btn.fire_event("click", None)

        return


class FileTile(sw.Tile):
    def __init__(self, tb_model, m):

        # gather model
        self.model = tb_model

        # get the map
        self.m = m

        # create widgets
        self.file_select = sw.LoadTableField()

        # bind it to the model
        self.alert = sw.Alert()

        self.model.bind(self.file_select, "json_table")

        # create the tile
        super().__init__(
            id_="file_widget",
            title=cm.table.title,
            btn=sw.Btn(cm.table.btn),
            alert=self.alert,
            inputs=[self.file_select],
        )

        # js behaviour
        self.btn.on_event("click", self._load_file)

    @su.loading_button()
    def _load_file(self, widget, event, data):

        # define variable
        table = self.model.json_table
        file = table["pathname"]
        lat = table["lat_column"]
        lng = table["lng_column"]
        id_ = table["id_column"]

        # check the variables
        if not self.alert.check_input(file, cm.table.not_a_file):
            return
        if not self.alert.check_input(lat, cm.table.missing_input):
            return
        if not self.alert.check_input(lng, cm.table.missing_input):
            return
        if not self.alert.check_input(id_, cm.table.missing_input):
            return

        # verify that they are all unique
        if len(set([lat, lng, id_])) != len([lat, lng, id_]):
            raise Exception(cm.table.repeated_input)

        # create the pts geodataframe
        df = pd.read_csv(file, sep=None, engine="python")
        df = df.filter(items=[lat, lng, id_])
        df = df.rename(columns={lat: "lat", lng: "lng", id_: "id"})
        gdf = gdp.GeoDataFrame(
            df, geometry=gdp.points_from_xy(df.lng, df.lat), crs="EPSG:4326"
        )

        # load the map
        cs.setMap(gdf, self.m)

        # set the dataframe in output
        self.model.pts = gdf

        self.alert.add_msg(cm.table.valid_columns, "success")

        return


class MapTile(sw.Tile):
    def __init__(self):

        # create the widgets
        self.map = sm.SepalMap()

        super().__init__(id_="file_widget", title=cm.table.map.title, inputs=[self.map])
