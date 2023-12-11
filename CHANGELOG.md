## 0.2.0 (2023-12-11)

### Feat

- use sepal_ui==2.17 to avoid conflicts with ipyleaflet
- use pre-commit hook

### Fix

- remove gdal from requirements
- list mosaics from planet
- adapt the proposed dates to the sensor availability Fix #82
- catch the flush error with a meaningful message Fix #81
- align items shape between the 2 drivers
- display images in chronological order FIx #80
- force id to be a key of the dataset fix #65

### Refactor

- remove debug arg
- remove unused files
