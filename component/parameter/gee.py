import datetime
from collections import OrderedDict

import ee

ee.Initialize()

# data parameters
gee_min_landsat_year = 1985  # launch of landsat 5
gee_min_sentinel_year = 2015  # launch of sentinel 2
gee_max_end_year = datetime.datetime.now().year
sources = ["landsat", "sentinel"]

# functions to access parameters according to the used satellite
def getSatellites(sources, year):

    satellites = OrderedDict()

    if "sentinel" in sources and year >= 2015:
        # cannot use SR as they don't cover years before 2020
        satellites["sentinel_2"] = "COPERNICUS/S2"
    if "landsat" in sources:
        if year >= 2013:
            satellites["landsat_8"] = "LANDSAT/LC08/C01/T1_SR"
        if year <= 2013:
            satellites["landsat_5"] = "LANDSAT/LT05/C01/T1_SR"
        if year >= 1999:
            satellites["landsat_7"] = "LANDSAT/LE07/C01/T1_SR"

    return satellites


def getShortname(satellite):
    short = {
        "sentinel_2": "S2",
        "landsat_5": "L5",
        "landsat_7": "L7",
        "landsat_8": "L8",
    }

    # in parralel sometime the code doesn't manage to write the appropriate key.
    # instead of crashing I'll just write nothing
    out = short[satellite] if satellite else ""

    return out


def getScale(satellite):

    scale = {"sentinel_2": 10, "landsat_5": 30, "landsat_7": 30, "landsat_8": 30}

    return scale[satellite]


def getAvailableBands():
    """give the bands composition for each name.
    0 being the landsat 7,
    1 landsat 5,
    2, landsat 8
    3: sentinel 2"""

    bands = {
        "Red, Green, Blue": {
            "landsat_7": ["B3", "B2", "B1"],
            "landsat_5": ["B3", "B2", "B1"],
            "landsat_8": ["B4", "B3", "B2"],
            "sentinel_2": ["B4", "B3", "B2"],
        },
        "Nir, Red, Green": {
            "landsat_7": ["B4", "B3", "B2"],
            "landsat_5": ["B4", "B3", "B2"],
            "landsat_8": ["B5", "B4", "B3"],
            "sentinel_2": ["B8", "B4", "B3"],
        },
        "Nir, Swir1, Red": {
            "landsat_7": ["B4", "B5", "B3"],
            "landsat_5": ["B4", "B5", "B3"],
            "landsat_8": ["B5", "B6", "B4"],
            "sentinel_2": ["B8", "B11", "B4"],
        },
        "Swir2, Nir, Red": {
            "landsat_7": ["B7", "B4", "B3"],
            "landsat_5": ["B7", "B4", "B3"],
            "landsat_8": ["B7", "B5", "B4"],
            "sentinel_2": ["B12", "B8", "B4"],
        },
        "Swir2, Swir1, Red": {
            "landsat_7": ["B7", "B5", "B3"],
            "landsat_5": ["B7", "B5", "B3"],
            "landsat_8": ["B7", "B6", "B4"],
            "sentinel_2": ["B12", "B11", "B4"],
        },
        "Swir2, Nir, Green": {
            "landsat_7": ["B7", "B4", "B2"],
            "landsat_5": ["B7", "B4", "B2"],
            "landsat_8": ["B7", "B5", "B3"],
            "sentinel_2": ["B12", "B8", "B3"],
        },
        "ndvi": {  # 2 useful bands nir and red
            "landsat_7": ["B4", "B3"],
            "landsat_5": ["B4", "B3"],
            "landsat_8": ["B5", "B4"],
            "sentinel_2": ["B8", "B4"],
        },
        "ndwi": {  # 2 useful bands nir and swir
            "landsat_7": ["B4", "B5"],
            "landsat_5": ["B4", "B5"],
            "landsat_8": ["B5", "B6"],
            "sentinel_2": ["B8", "B11"],
        },
    }

    return bands


def getCloudMask(satelliteId):
    """return the cloud masking function adapted to the apropriate satellite"""

    if satelliteId in ["landsat_5", "landsat_7"]:

        def cloudMask(image):
            qa = image.select("pixel_qa")
            # If the cloud bit (5) is set and the cloud confidence (7) is high
            # or the cloud shadow bit is set (3), then it's a bad pixel.
            cloud = qa.bitwiseAnd(1 << 5).Or(qa.bitwiseAnd(1 << 3))
            # .And(qa.bitwiseAnd(1 << 7)) \
            # Remove edge pixels that don't occur in all bands
            mask2 = image.mask().reduce(ee.Reducer.min())

            return image.updateMask(cloud.Not()).updateMask(mask2)

    elif satelliteId == "landsat_8":

        def cloudMask(image):
            # Bits 3 and 5 are cloud shadow and cloud, respectively.
            cloudShadowBitMask = 1 << 3
            cloudsBitMask = 1 << 5
            # Get the pixel QA band.
            qa = image.select("pixel_qa")
            # Both flags should be set to zero, indicating clear conditions.
            mask = (
                qa.bitwiseAnd(cloudShadowBitMask)
                .eq(0)
                .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
            )

            return image.updateMask(mask)

    elif satelliteId == "sentinel_2":

        def cloudMask(image):
            qa = image.select("QA60")
            # Bits 10 and 11 are clouds and cirrus, respectively.
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            # Both flags should be set to zero, indicating clear conditions.
            mask = (
                qa.bitwiseAnd(cloudBitMask)
                .eq(0)
                .And(qa.bitwiseAnd(cirrusBitMask).eq(0))
            )

            return image.updateMask(mask)  # .divide(10000)

    return cloudMask


# legacy viz params for vizualisation
def vizParam(bands, buffer, image, satellite):

    if not bands:  # didn't find images for the sample
        return {}

    return {"min": 0, "max": 3000, "bands": bands}
