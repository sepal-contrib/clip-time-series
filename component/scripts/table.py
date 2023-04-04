import shutil

from ipyleaflet import AwesomeIcon, GeoJSON, Marker, MarkerCluster
from ipywidgets import HTML
from sepal_ui import color
from sepal_ui import mapping as sm

from component import parameter as cp
from component.message import cm

STYLE = {
    "stroke": True,
    "color": color.secondary,
    "weight": 2,
    "opacity": 1,
    "fill": True,
    "fillColor": color.secondary,
    "fillOpacity": 0.4,
}

ICON = AwesomeIcon(name="", icon_color="white", marker_color="darkblue")


def setMap(model, m: sm.SepalMap):
    """create a map and a df list of points."""
    # empty the map
    m.remove_all()

    # add markers in case of points
    if model.types == cp.types[0]:

        # add the pts on the map
        markers = []
        for index, row in model.raw_geometry.iterrows():

            msg = HTML(value=f"id: {row.id}")
            marker = Marker(
                icon=ICON, popup=msg, location=(row.lat, row.lng), draggable=False
            )
            markers.append(marker)

        # display on the map
        marker_cluster = MarkerCluster(markers=tuple(markers))
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
