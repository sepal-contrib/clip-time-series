# set the years that will be used with planet data
planet_min_start_year = 2016
planet_max_end_year = 2021

# to each year select a date range that will match a basempa included in the SEPAL NICFI contract
planet_date_ranges = {
    2016: {"S1": "2015-12_2016-05", "S2": "2016-06_2016-11"},
    2017: {"S1": "2016-12_2017-05", "S2": "2017-06_2017-11"},
    2018: {"S1": "2017-12_2018-05", "S2": "2018-06_2018-11"},
    2019: {"S1": "2018-12_2019-05", "S2": "2019-06_2019-11"},
    2020: {"S1": "2019-12_2020-05", "S2": "2020-06_2020-08"},
    2021: {"S1": "2021-01", "S2": "2021-03"},
}

planet_bands_combo = {"rgb": [1, 2, 3], "cir": [4, 1, 2]}

planet_semesters = {"S1": "Semester 1", "S2": "Semester 2"}
