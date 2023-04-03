"""Module to gather all scripts of the application.

If you only have few widgets, a module is not necessary and you can simply use a scripts.py file
In a big module with lot of custom scripts, it can make sense to split things in separate files for the sake of maintenance

If you use a module import all the functions here to only have 1 call to make
"""

from .export import *
from .table import *
from .vizualisation import *
from .gee import *
from .planet import *
