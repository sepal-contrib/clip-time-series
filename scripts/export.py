import pandas as pd
from utils import gdrive
from utils import utils
import ee 
from pathlib import Path
from sepal_ui.scripts import utils as su
from matplotlib.backends.backend_pdf import PdfPages
from utils import parameters as pm
import time
import matplotlib.pyplot as plt
import rasterio as rio
import numpy as np
import os

ee.Initialize()

def getImage(bands, sources, year):
    
    #check only for landsats satelites at the moment
    dataset_source, bandId = pm.getSatelites(year)
    viz_bands = pm.getAvailableBands()[bands][bandId]
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    dataset = ee.ImageCollection(dataset_source)
    dataset = dataset.filterDate(start, end).median()
    select = dataset.select(viz_bands)
    
    return select
    

def run(file, bands, sources, output):
    
    start_year = 2005
    end_year = 2020
    
    #get the filename
    filename = Path(file).stem
    
    #extract the bands to use them in names 
    name_bands = '_'.join(bands.split(', '))
    
    #pdf name 
    pdf_file = pm.getResultDir() + '{}_{}.pdf'.format(filename, name_bands)
    
    if os.path.isfile(pdf_file):
        return pdf_file
    
    #start the drive handler 
    drive_handler = gdrive.gdrive()
    
    #read the points 
    pts = pd.read_csv(file)
    
    #transform them in ee points 
    ee_pts = [ee.Geometry.Point(pts.loc[i]['lng'], pts.loc[i]['lat']) for i in range(len(pts))]
    
    #create the buffers 
    buffers = [ee_pt.buffer(2000) for ee_pt in ee_pts]
    
    #create a filename list 
    descriptions = {}
    for index, row in pts.iterrows():
        descriptions[index] = {}
        for year in range(start_year, end_year):
            descriptions[index][year] = '{}_pt_{}_{}_{}'.format(filename, index, name_bands, year)
    
    #load all the data in gdrive 
    for index, row in pts.iterrows():
        for year in range(start_year, end_year):
            
            image = getImage(bands, sources, year)
            
            task_config = {
                'image':image,
                'description': descriptions[index][year],
                'scale': 30,
                'region': buffers[index]
            }
            
            task = ee.batch.Export.image.toDrive(**task_config)
            task.start()
            su.displayIO(output, 'exporting pt: {} for year: {}'.format(index, year))
    
    #check the exportation evolution 
    task_list = []
    for index, row in pts.iterrows():
        for year in range(start_year, end_year):
            task_list.append(descriptions[index][year])
            
    state = utils.custom_wait_for_completion(task_list, output)
    su.displayIO(output, 'Export to drive finished', 'success')
    time.sleep(2)
    
    su.displayIO(output, 'Retreive to sepal')
    #retreive all the file ids 
    filesId = []
    for index, row in pts.iterrows():
        for year in range(start_year, end_year):
            filesId += drive_handler.get_files(descriptions[index][year])
    #download the files        
    drive_handler.download_files(filesId, pm.getTmpDir())     
    #remove the files from gdrive 
    drive_handler.delete_files(filesId)
    
    #create the resulting pdf
    with PdfPages(pdf_file) as pdf:
        #each point is display on one single page
        for index, row in pts.iterrows():
            
            page_title = "Pt_{} (lat:{:.5f}, lng:{:.5f})".format(index+1, row['lat'], row['lng'])
            su.displayIO(output, 'Creating page for pt {}'.format(index))
            fig, axes = plt.subplots(3, 5, figsize=(11.69,8.27))
            fig.suptitle(page_title, fontsize=16)
            
            #display the images in a fig and export it as a pdf page
            for year in range(start_year, end_year):
                
                file = pm.getTmpDir() + descriptions[index][year] + '.tif'
    
                with rio.open(file) as f:
                    data = f.read([1, 2, 3], masked=True)
                
                data = data/3000
                data = data.clip(0, 1)
                data = np.transpose(data,[1,2,0])
            
                i = year - start_year
                ax = axes[pm.getPositionPdf(i)[0], pm.getPositionPdf(i)[1]]
                ax.imshow(data)
                ax.set_title(str(year))
                ax.axis('off')
                
                #delete the tmp file ( TODO maybe only flush it once)
                os.remove(file)
            
            #save the page 
            pdf.savefig(fig)
            plt.close()
    
    su.displayIO(output, 'PDF output finished', 'success')
    
    return pdf_file
    
    
    