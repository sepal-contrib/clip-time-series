Clip time series
================

.. tip::

    This documentation should explain every step to execute the module. If any question or bug remains, please consider post it on the `bug report page <https://github.com/openforis/clip-time-series/issues/new>`_.

This module allows the user to download as a :code:`.pdf` an auto generated time series from customizable dates. 
Each mosaic will be represented in a square of custom size from **500x500m** to **1000x10000km** around the point of interest using the band combination selected by the user. 


Select file 
-----------

First the user needs to select a file. This file will be the main input of the module and each page of the final :code:`.pdf` will match a geometry of the input. The user can use 2 types of input: 

-   Table file (:code:`.csv`, :code:`.txt`) containing at least coordinates and ID columns
-   Shapes (:code:`.geojson`, :code:`.shp`, :code:`.geopackage`) with at least geometry and Id column

Table
*****

Select the :guilabel:`point` radio button.

The table file can be :code:`.csv` or :code:`.txt`. It needs to have at least 3 columns including the latitude coordinates, the longitude coordinates and an Id. the name of the columns can be anything. 

.. warning::

    The table coordinates need to remain unprojected, i.e. in EPSG:4326
    
Select the file by clicking :guilabel:`Table file`. Only the matching file type will be displayed. User can navigate through its SEPAL folders to find the appropriate table. 

One a file is selected, the widget will try to autopopulate the id, latitude and longitude columns. If columns are wrongly set of if data are missing the user need to select one of the file column to completely describe the points (x, y, id).

.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/input_table.png
    :alt: input table
    
Click on :guilabel:`load your pts file` to load the points as a geodataframe in the app model and display them on a map. 
The points will be represented as marker clusters and the map will automatically zoom on them. click on any cluster to zoom in. 

.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/map_table.png

.. tip::

    Click on :guilabel:` download test dataset` will automatically download and validate a set of point in the app. Use it to discover the module functionalities.
    
Shape
*****

Select the :guilabel:`shape` radio button.

The table file can be any file type digested by the :code:`fiona` librairy. The file need to have at least 1 column to describe the Id.

The Id column will be used to name the points in the final pdf. Select it in the updated dropdown menu "Id column". 

.. warning::

    if you use names for `id` make sure that they are all unique. 

.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/input_shape.png
    :alt: input_shape

Click on :guilabel:`load your pts file` to load the shapes as a geodataframe in the app model and display them on a map. The map will be updated with the selected shapes and zoom on the area of interes.

.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/map_shape.png
    :alt: map_shape

Select time serie parameters
----------------------------

In this second step, the user is asked to select the parameters of its time series.

drivers
*******

2 drivers are available in this module. You can select either a GEE based computation (images will be retreived from GEE) or planet (images will be retreived from planet servers using the user API key). 

If the user selects :guilabel:`gee`, the panel will ask you to select the satellites you want to use for the thumbnails. you can select any satellites imagery from landsat family and Sentinel program. 

The best available image is then selected using the following hierarchy order: 

- Sentinel 2
- Landsat 8
- landsat 5
- landsat 7

If the user select :guilabel:`planet`, the panel will ask for the Planet API key.

points
******

The number of points a user wants to display can vary. If the user select all then all the available points in the provided file will be used. It's also possible to select a subset of them using there **id** names. 

bands
*****

multiple band combination can be selected:

-   Using the :code:`gee` driver:

    -   Red, Green, Blue
    -   Nir, Red, Green
    -   Nir, Swir1, Red 
    -   Swir2, Nir, Red 
    -   Swir2, Swir1, Red
    -   Swir2, Nir, Green
    
-   Using the :code:`planet` driver:

    -   rgb
    -   cir

mosaics
*******

Each selected mosaics will be represented by a thumbnail in the final :code:`pdf`. 

.. warning::

    User can select as many mosaics as he wants but note:
    
    -   The page will remain in A4 format so the thumbnails will become smaller and smaller proportionnaly to the number of mosaics.
    -   Each image needs to be downloaded to SEPAL so many images => longer compuation time
    
Using the :code:`gee` driver, mosaics are yearly cloudless mosaics build on the best found satellites as described in the previous section.

Using the :code:`planet`driver, 3 types of mosaics can be selected (and mixed together):

-   NICFI bianual mosaics
-   NICFI monthly mosaics
-   Other (any other mosaics associated to the user API key)

thumbnails
**********

Select a thumbnail size. This will be the minimal size of the thumbnail used. If the shape defined in the first panel is bigger then the software will try to fint he smallest square around the shape centered on the centroid of the shape.

.. danger::

    if the final outter square of a shape is bigger than **10000x10000km**, gee and planet will refuse to export your data. Remember that this module is not meant to export national time series but thumbnails.

square size
***********

In the middle of the final image, the software will display a small square to visually represent the point. User can select the size of this square depending on the size of its thumbnails. 

If the used dataset is shapefile then the square will be replace by the shape geometry.



When you click on the validation button, the module gives you a sum up of the download your about to perform. It's a warning step to avoid the download of huge number of points on wrongly defined parameters. 

.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/viz_gee.png
    :alt: viz



Export data
-----------

Only one single button here. Click on it and the downloading of your images will be send to earthengine or planet.

.. danger::

    The build of the :code:`.pdf` file can consume lots of computation resources and in particular RAM. if you're module freezes more than 2-3 minutes you certainly ran out of memory and the Python kernel have died. Restart the process with a bigger instance.
    
.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/process_loading.png
    :alt: process_loading

.. note:: 

    The images will be removed from your gdrive after the creation of the pdf to save space

Then the module will give you a clickable link in the green button and a preview of the first page of the :code:`pdf`

.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/output_shape_planet.png
    :alt: results
    :width: 49%
    
.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/output_table_planet.png
    :alt: results
    :width: 49%
    
.. image:: https://raw.githubusercontent.com/openforis/clip-time-series/master/doc/img/output_table_landsat.png
    :alt: results
    :width: 49%
