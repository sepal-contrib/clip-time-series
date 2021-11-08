import os
from pathlib import Path
import shutil

import pandas as pd
import geemap
from ipyleaflet import GeoJSON, MarkerCluster, Marker
from sepal_ui import color

from component.message import cm
from component import parameter as cp

STYLE = {
    "stroke": True,
    "color": color.success,
    "weight": 2,
    "opacity": 1,
    "fill": True,
    "fillColor": color.success,
    "fillOpacity": 0.4,
}


def setMap(model, m):
    """create a map and a df list of points"""

    # empty the map
    for l in m.layers:
        if l.name != "CartoDB.DarkMatter":
            m.remove_layer(l)

    # add markers in case of points
    if model.types == cp.types[0]:

        # add the pts on the map
        markers, popups = [], []
        for index, row in model.raw_geometry.iterrows():
            marker = Marker(location=(row.lat, row.lng), draggable=False)
            markers.append(marker)
            popups.append(row.id)

        # display on the map
        marker_cluster = MarkerCluster(markers=tuple(markers), popups=popups)
        m.add_layer(marker_cluster)

    # add the vector as a geojson
    elif model.types == cp.types[1]:

        data = model.raw_geometry.__geo_interface__
        layer = GeoJSON(data=data, style=STYLE, name="shapes")
        m.add_layer(layer)

    # recenter the map
    m.zoom_bounds(model.raw_geometry.total_bounds)

    return


def download_test_file(output):

    # download the file to the download directory
    shutil.copy(cp.test_dataset, cp.sepal_down_dir)

    dst = cp.sepal_down_dir / cp.test_dataset.name

    # update the output
    output.add_live_msg(cm.table.test.msg.format(dst), "success")

    return dst
