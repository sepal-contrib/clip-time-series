import pytest
import geopandas as gpd
import component.widget as cw
import io
import os

from sepal_ui.planetapi import PlanetModel


@pytest.fixture
def geometries():

    json_file = io.StringIO(
        """{"type": "FeatureCollection", "features": [{"id": "0", "type": "Feature", "properties": {"lat": 5.33469724544027, "lng": 13.0256336559457, "id": 1}, "geometry": {"type": "Point", "coordinates": [13.0256336559457, 5.33469724544027]}}, {"id": "1", "type": "Feature", "properties": {"lat": 5.31724397918854, "lng": 13.0145627442248, "id": 2}, "geometry": {"type": "Point", "coordinates": [13.0145627442248, 5.31724397918854]}}, {"id": "2", "type": "Feature", "properties": {"lat": 5.31816258449969, "lng": 13.0320916877829, "id": 3}, "geometry": {"type": "Point", "coordinates": [13.0320916877829, 5.31816258449969]}}, {"id": "3", "type": "Feature", "properties": {"lat": 5.48440733356101, "lng": 12.9075439309229, "id": 4}, "geometry": {"type": "Point", "coordinates": [12.9075439309229, 5.48440733356101]}}, {"id": "4", "type": "Feature", "properties": {"lat": 5.46236646346553, "lng": 12.9093890828764, "id": 5}, "geometry": {"type": "Point", "coordinates": [12.9093890828764, 5.46236646346553]}}]}"""
    )

    return gpd.read_file(json_file)


@pytest.fixture
def alert():
    return cw.CustomAlert()


@pytest.fixture
def planet_model():
    # Get planet api key from the environment
    api_key = os.getenv("PLANET_API_KEY")
    return PlanetModel(api_key)
