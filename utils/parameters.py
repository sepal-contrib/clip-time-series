# hard coded parameters
import os
import glob
import ee
from pathlib import Path

ee.Initialize()

##########################
##       function       ##
##########################
def getPositionPdf(i):
    """Return the position of the square on the pdf page"""
    return [int(i / 5), i % 5]
