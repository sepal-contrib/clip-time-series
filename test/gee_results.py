"mosaics, image_size, sources, bands, square_size"
import ee


a_inputs = [2024], 250, ["landsat"], "Red, Green, Blue", 90


def a_expected_vrt_list(tmp_dir):
    return {
        2024: tmp_dir / "test_points_landsat_Red_Green_Blue_sqSize90_size250_2024.vrt"
    }


a_expected_title_list = {
    2024: {
        0: "2024 L9",
        1: "2024 L9",
        2: "2024 L9",
        3: "2024 L9",
        4: "2024 L9",
    }
}


# test with more than one year

b_inputs = [2024, 2023], 500, ["landsat"], "Red, Green, Blue", 90


def b_expected_vrt_list(tmp_dir):
    return {
        2024: tmp_dir / "test_points_landsat_Red_Green_Blue_sqSize90_size500_2024.vrt",
        2023: tmp_dir / "test_points_landsat_Red_Green_Blue_sqSize90_size500_2023.vrt",
    }


b_expected_title_list = {
    2023: {
        0: "2023 L9",
        1: "2023 L9",
        2: "2023 L9",
        3: "2023 L9",
        4: "2023 L9",
    },
    2024: {
        0: "2024 L9",
        1: "2024 L9",
        2: "2024 L9",
        3: "2024 L9",
        4: "2024 L9",
    },
}


# Test with sentinel

c_inputs = [2024], 250, ["sentinel"], "Red, Green, Blue", 90


def c_expected_vrt_list(tmp_dir):
    return {
        2024: tmp_dir / "test_points_sentinel_Red_Green_Blue_sqSize90_size250_2024.vrt"
    }


c_expected_title_list = {
    2024: {
        0: "2024 S2",
        1: "2024 S2",
        2: "2024 S2",
        3: "2024 S2",
        4: "2024 S2",
    }
}


# Test with multiple years

d_inputs = [2019, 2021], 250, ["sentinel", "landsat"], "Red, Green, Blue", 90


def d_expected_vrt_list(tmp_dir):
    return {
        2019: tmp_dir
        / "test_points_sentinel_landsat_Red_Green_Blue_sqSize90_size250_2019.vrt",
        2021: tmp_dir
        / "test_points_sentinel_landsat_Red_Green_Blue_sqSize90_size250_2021.vrt",
    }


d_expected_title_list = {
    2019: {
        0: "2019 S2",
        1: "2019 S2",
        2: "2019 S2",
        3: "2019 S2",
        4: "2019 S2",
    },
    2021: {
        0: "2021 S2",
        1: "2021 S2",
        2: "2021 S2",
        3: "2021 S2",
        4: "2021 S2",
    },
}

######################################################

test_ee_buffer = ee.Geometry.Polygon(
    [
        [
            [13.024513100356552, 5.333572819469696],
            [13.026757769061255, 5.333572819469696],
            [13.026757769061255, 5.335822103684232],
            [13.024513100356552, 5.335822103684232],
            [13.024513100356552, 5.333572819469696],
        ]
    ]
)
