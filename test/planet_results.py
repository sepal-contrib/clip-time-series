"mosaics, image_size, bands",

a_inputs = (
    [
        "planet_medres_normalized_analytic_2020-10_mosaic",
        "planet_medres_normalized_analytic_2020-09_mosaic",
        "planet_medres_normalized_analytic_2020-11_mosaic",
        "planet_medres_normalized_analytic_2020-12_mosaic",
    ],
    250,
    "cir",
)


def a_expected_vrt_list(tmp_dir):
    return {
        "planet_medres_normalized_analytic_2020-10_mosaic": tmp_dir
        / "test_points_planet_cir_size250_planet_medres_normalized_analytic_2020-10_mosaic.vrt",
        "planet_medres_normalized_analytic_2020-09_mosaic": tmp_dir
        / "test_points_planet_cir_size250_planet_medres_normalized_analytic_2020-09_mosaic.vrt",
        "planet_medres_normalized_analytic_2020-11_mosaic": tmp_dir
        / "test_points_planet_cir_size250_planet_medres_normalized_analytic_2020-11_mosaic.vrt",
        "planet_medres_normalized_analytic_2020-12_mosaic": tmp_dir
        / "test_points_planet_cir_size250_planet_medres_normalized_analytic_2020-12_mosaic.vrt",
    }


a_expected_title_list = {
    "planet_medres_normalized_analytic_2020-10_mosaic": {
        0: "Oct 2020",
        1: "Oct 2020",
        2: "Oct 2020",
        3: "Oct 2020",
        4: "Oct 2020",
    },
    "planet_medres_normalized_analytic_2020-09_mosaic": {
        0: "Sep 2020",
        1: "Sep 2020",
        2: "Sep 2020",
        3: "Sep 2020",
        4: "Sep 2020",
    },
    "planet_medres_normalized_analytic_2020-11_mosaic": {
        0: "Nov 2020",
        1: "Nov 2020",
        2: "Nov 2020",
        3: "Nov 2020",
        4: "Nov 2020",
    },
    "planet_medres_normalized_analytic_2020-12_mosaic": {
        0: "Dec 2020",
        1: "Dec 2020",
        2: "Dec 2020",
        3: "Dec 2020",
        4: "Dec 2020",
    },
}
