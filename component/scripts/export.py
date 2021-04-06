from pathlib import Path
from urllib.request import urlretrieve
import zipfile

import ee 
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import rasterio as rio
from rasterio.windows import from_bounds
import numpy as np
from shapely import geometry as sg
from PyPDF2 import PdfFileMerger, PdfFileReader
from osgeo import gdal

from component import parameter as cp

ee.Initialize()    

def getImage(sources, bands, mask, year):
    
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'
    
    #priority selector for satellites
    satellites = cp.getSatellites(sources, year)
    for satelliteId in satellites:
        dataset = ee.ImageCollection(satellites[satelliteId]) \
            .filterDate(start, end) \
            .filterBounds(mask) \
            .map(cp.getCloudMask(satelliteId))
        
        if dataset.size().getInfo() > 0:
            satellite = satelliteId
            break
            
    clip = dataset.median().clip(mask).select(cp.getAvailableBands()[bands][satelliteId])
    
    return (clip, satelliteId)
    

def run(file, pts, bands, sources, start, end, square_size, output):
    
    # check dates 
    start_year = max(start, cp.min_start_year)
    end_year = min(end, cp.max_end_year)
    range_year = [y for y in range(start_year, end_year + 1)]
    
    # get the filename
    filename = Path(file).stem
    
    # extract the bands to use them in names 
    name_bands = '_'.join(bands.split(', '))
    
    # pdf name 
    pdf_file = cp.result_dir.joinpath(f'{filename}_{name_bands}_{start_year}_{end_year}.pdf')
    
    if pdf_file.is_file():
        output.add_live_msg('Pdf already exist', 'success')
        return pdf_file
    
    # transform the stored points into ee points 
    ee_pts = [ ee.Geometry.Point(row.lng, row.lat) for _, row in pts.iterrows()]
    
    # create the square buffers 
    ee_buffers = [ee_pt.buffer(square_size).bounds() for ee_pt in ee_pts]
    
    # create a multipolygon mask
    ee_multiPolygon = ee.Geometry.MultiPolygon(ee_buffers).dissolve(maxError=100)     
            
    # create a filename list 
    descriptions = {}
    for year in range_year:
        descriptions[year] = f'{filename}_{name_bands}_{year}'
        
    # load the data directly in SEPAL
    satellites = {} # contain the names of the used satellites
    task_list = []
    total_images = (end_year - start_year + 1)*(len(ee_buffers)-1)
    for i, year in enumerate(range_year):
        
        image, satellites[year] = getImage(sources, bands, ee_multiPolygon, year)
        
        for j, buffer in enumerate(ee_buffers):
            
            description = f"{descriptions[year]}_{j}"
            
            dst = cp.tmp_dir.joinpath(f'{description}.tif')
            
            if not dst.is_file():
                
                name = 'zipimage'
                
                link = image.getDownloadURL({
                    'name': name,
                    'region': buffer,
                    'filePerBand': False,
                    'scale': cp.getScale(satellites[year])
                })
                
                tmp = cp.tmp_dir.joinpath(f'{name}.zip')
                urlretrieve (link, tmp)
                
                # unzip the file 
                with zipfile.ZipFile(tmp,"r") as zip_:
                    data = zip_.read(zip_.namelist()[0])
                    
                    with dst.open('wb') as f:
                        f.write(data)
                
                # remove the zip 
                tmp.unlink()
            
            output.update_progress((i*(len(ee_buffers)-1) + j)/total_images, msg='Image loaded')
    
    # create a single vrt per year 
    for year in range_year:
        # retreive the vrt 
        vrt_path = cp.tmp_dir.joinpath(f'{descriptions[year]}.vrt')
        
        # retreive the filepaths
        filepaths = [str(f) for f in cp.tmp_dir.glob(f'{descriptions[year]}_*.tif')]
        
        # build the vrt
        ds = gdal.BuildVRT(str(vrt_path), filepaths)
        ds.FlushCache()
        
        # check that the file was effectively created (gdal doesn't raise errors)
        if not vrt_path.is_file():
            raise Exception(f"the vrt {vrt_path} was not created")
        
    nb_col, nb_line = cp.get_dims(end_year - start_year)
    
    pdf_tmps = []
    output.update_progress(0, msg='Pdf page created')
    for index, row in pts.iterrows():
        
        pdf_tmp = cp.tmp_dir.joinpath(f'{filename}_{name_bands}_tmp_pts_{row["id"]}.pdf')
        pdf_tmps.append(pdf_tmp)
    
        # create the resulting pdf
        with PdfPages(pdf_tmp) as pdf:        
            
            page_title = f"Pt_{row['id']} (lat:{row['lat']:.5f}, lng:{row['lng']:.5f})"
                  
            fig, axes = plt.subplots(nb_line, nb_col, figsize=(11.69,8.27), dpi=500)
            fig.suptitle(page_title, fontsize=16, fontweight ="bold")
            fig.set_tight_layout(True) 
            # display the images in a fig and export it as a pdf page
            placement_id = 0
            for year in range_year:
                
                # load the file 
                file = cp.tmp_dir.joinpath(f'{descriptions[year]}.vrt')
                
                # extract the buffer bounds 
                coords = ee_buffers[index].coordinates().get(0).getInfo()
                bl, tr = coords[0], coords[2]
            
                with rio.open(file) as f:
                    data = f.read(window=from_bounds(bl[0], bl[1], tr[0], tr[1], f.transform))
                
                bands = [] 
                for i in range(3):
                    band = data[i]
                    # remove the NaN from the analysis
                    h_, bin_ = np.histogram(band[np.isfinite(band)].flatten(), 3000, density=True) 
    
                    cdf = h_.cumsum() # cumulative distribution function
                    cdf = 3000 * cdf / cdf[-1] # normalize
    
                    # use linear interpolation of cdf to find new pixel values
                    band_equalized = np.interp(band.flatten(), bin_[:-1], cdf)
                    band_equalized = band_equalized.reshape(band.shape)
        
                    bands.append(band_equalized)
    
                data = np.stack( bands, axis=0 )

                data = data/3000
                data = data.clip(0, 1)
                data = np.transpose(data,[1,2,0])
            
                place = cp.getPositionPdf(placement_id, nb_col) 
                ax = axes[place[0], place[1]]
                ax.imshow(data, interpolation='nearest')
                ax.set_title(str(year) + ' ' + cp.getShortname(satellites[year]), x=.0, y=1.0, fontsize='small', backgroundcolor='white', ha='left')
                ax.axis('off')
                ax.set_aspect('equal', 'box')
                
                # increment the placement image 
                placement_id += 1
            
            # finish the file with empty plots if needed
            while placement_id < nb_line * nb_col:
                place = cp.getPositionPdf(placement_id, nb_col) 
                ax = axes[place[0], place[1]]
                ax.axis('off')
                ax.set_aspect('equal', 'box')
                
                placement_id += 1
            
            # save the page
            pdf.savefig(fig)
            plt.close('all')
           
        progress = index/(len(pts) - 1) if len(pts) > 1 else 1
        output.update_progress(progress, msg='Pdf page created')
        
    # merge all the pdf files 
    output.add_live_msg('merge all pdf files')
    mergedObject = PdfFileMerger()
    for pdf in pdf_tmps:
        mergedObject.append(PdfFileReader(str(pdf), 'rb'))
        pdf.unlink()
    mergedObject.write(str(pdf_file))
    
    # flush the tmp repository 
    for file in cp.tmp_dir.glob('*.*'):
        file.unlink()
    #cp.tmp_dir.rmdir() # if I remove the folder I will not be able to relaunch the app without relaunhing everything
    
    output.add_live_msg('PDF output finished', 'success')
    
    return pdf_file    