# the drivers that can be used to create thumbnails
drivers = ["gee", "planet"]

# the file types that can be digested by the app
types = ["points", "shapes"]

# define the extrems size of the thumbnails
min_image = 500
max_image = 10000

# define the extreme size of the square
min_square = 10
max_square = 500

# the color and size wich will be used for the display of the polygon
polygon_colors = {
    "Red, Green, Blue": "blue",
    "Nir, Red, Green": "yellow",
    "Nir, Swir1, Red": "yellow",
    "Swir2, Nir, Red": "yellow",
    "Swir2, Swir1, Red": "yellow",
    "Swir2, Nir, Green": "yellow",
    "rgb": "blue",
    "cir": "yellow",
    "ndvi": "red",
    "ndwi": "red",
}
polygon_width = 2

# the basemap used in the file tile
basemap = "Esri.WorldImagery"
