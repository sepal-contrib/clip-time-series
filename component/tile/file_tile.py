import json

from sepal_ui import sepalwidgets as sw 
from sepal_ui import mapping as sm
import pandas as pd
import geopandas as gdp
import ipyvuetify as v

from component import scripts as cs
from component.message import cm

class TestTile(sw.Tile):
    
    def __init__(self):
        
        # create the widgets 
        txt = sw.Markdown(cm.table.test.txt) 
        
        # create the tile
        super().__init__(
            id_ = 'file_widget',
            title = cm.table.test.title,
            output = sw.Alert(),
            btn = sw.Btn(cm.table.test.btn, outlined=True, small=True),
            inputs = [txt]
        )
        
        # js behaviour 
        self.btn.on_event('click', self._import_test_file)
        
    def _import_test_file(self, widget, event, data):

        widget.toggle_loading()

        # download the test dataset to the download folder 
        test_file = cs.download_test_file(self.output)
    
        # add the file name to the file selector
        # need to update the fileinput component
    
        widget.toggle_loading()
    
        return 
        
class FileTile(sw.Tile):
    
    def __init__(self, tb_io, m):
        
        # gather io
        self.io = tb_io
        
        # get the map 
        self.m = m
        
        # create widgets 
        file_select = sw.LoadTableField()
        
        # bind it to the io 
        output = sw.Alert() \
            .bind(file_select, self.io, 'json_table')
        
        # create the tile 
        super().__init__(
            id_ = 'file_widget',
            title = cm.table.title,
            btn = sw.Btn(cm.table.btn),
            output = output,
            inputs = [file_select]
        )
        
        # js behaviour 
        self.btn.on_event('click', self._load_file)
        
    def _load_file(self, widget, event, data):
    
        # toggle the loading button 
        widget.toggle_loading()
    
        # define variable 
        table = json.loads(self.io.json_table)
        file = table['pathname']
        lat = table['lat_column']
        lng = table['lng_column']
        id_ = table['id_column']
    
    
        # check the variables 
        if not self.output.check_input(file, cm.table.not_a_file): return widget.toggle_loading()
        if not self.output.check_input(lat, cm.table.missing_input): return widget.toggle_input()
        if not self.output.check_input(lng, cm.table.missing_input): return widget.toggle_input()
        if not self.output.check_input(id_, cm.table.missing_input): return widget.toggle_input()    
    
        # verify that they are all unique
        if len(set([lat, lng, id_])) != len([lat, lng, id_]): 
            self.output.add_msg(cm.table.repeated_input, 'error')
            return widget.toggle_loading()
    
        try:
            # create the pts geodataframe
            df = pd.read_csv(file, sep=None, engine='python')
            df = df.filter(items=[lat, lng, id_])
            df = df.rename(columns={lat: 'lat', lng: 'lng', id_: 'id'})
            gdf = gdp.GeoDataFrame(df, geometry=gdp.points_from_xy(df.lng, df.lat), crs='EPSG:4326')
    
            # load the map
            cs.setMap(gdf, self.m) 
    
            # set the dataframe in output 
            self.io.pts = gdf
    
            self.output.add_msg(cm.table.valid_columns, 'success')
        
        except Exception as e: 
            self.output.add_live_msg(str(e), 'error')
    
        # toggle the loading button 
        widget.toggle_loading()
    
        return
        
class MapTile(sw.Tile):
    
    def __init__(self):
        
        # create the widgets 
        self.map = sm.SepalMap()
        
        super().__init__(
            id_ = "file_widget",
            title = cm.table.map.title,
            inputs = [self.map]
        )

    