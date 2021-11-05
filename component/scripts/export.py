from pathlib import Path
from unidecode import unidecode
import re

import ee
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import rasterio as rio
from rasterio.windows import from_bounds
from rasterio import warp
from rasterio.crs import CRS
import numpy as np
from shapely import geometry as sg
from PyPDF2 import PdfFileMerger, PdfFileReader
import geopandas as gpd

from component import parameter as cp

ee.Initialize()


def is_pdf(file, bands):
    """check if the pdf is already existing, return false if not"""

    # get the filename
    filename = Path(file).stem

    # extract the bands to use them in names
    name_bands = "_".join(bands.split(", "))

    # pdf name
    pdf_file = cp.result_dir.joinpath(f"{filename}_{name_bands}.pdf")

    return pdf_file.is_file()


def get_pdf(
    file, mosaics, image_size, square_size, vrt_list, title_list, bands, pts, output
):

    # get the filename
    filename = Path(file).stem

    # extract the bands to use them in names
    name_bands = "_".join(bands.split(", "))

    # pdf name
    pdf_file = cp.result_dir / f"{filename}_{name_bands}.pdf"

    # create a geopandas of square buffer
    # they will only be used in 3857 no need to reproject to 4326
    gdf_squares = pts.to_crs("EPSG:3857")
    gdf_squares["geometry"] = gdf_squares.buffer(square_size / 2, cap_style=3)
    # gdf_squares = gdf_squares.to_crs("EPSG:4326")

    # create a geopandas of thumbnails buffer
    gdf_buffers = pts.to_crs("EPSG:3857")
    gdf_buffers["geometry"] = gdf_buffers.buffer(image_size / 2, cap_style=3)
    gdf_buffers = gdf_buffers.to_crs("EPSG:4326")

    # get the disposition in col and line
    nb_col, nb_line = cp.get_dims(len(mosaics))

    pdf_tmps = []
    output.reset_progress(len(pts), "Pdf page created")
    for index, row in gdf_buffers.iterrows():

        name = re.sub("[^a-zA-Z\d\-\_]", "_", unidecode(str(row["id"])))

        pdf_tmp = cp.tmp_dir / f"{filename}_{name_bands}_tmp_pts_{name}.pdf"
        pdf_tmps.append(pdf_tmp)

        if pdf_tmp.is_file():
            continue

        # create the resulting pdf
        with PdfPages(pdf_tmp) as pdf:

            page_title = f"Pt_{name} (lat:{row['lat']:.5f}, lng:{row['lng']:.5f})"

            fig, axes = plt.subplots(
                nb_line, nb_col, figsize=(11.69, 8.27), dpi=500, constrained_layout=True
            )

            # I reshape by default to avoid a crash
            # if nb_line = 1 the dimension of the table is reduced
            axes = np.array(axes, dtype=object).reshape(nb_line, nb_col)

            fig.suptitle(page_title, fontsize=16, fontweight="bold")
            # fig.set_tight_layout(True)

            # display the images in a fig and export it as a pdf page
            placement_id = 0

            for m in mosaics:

                # load the file
                file = vrt_list[m]

                # extract the buffer bounds
                bounds = row["geometry"].bounds

                with rio.open(file) as f:
                    data = f.read(window=from_bounds(*bounds, f.transform))

                    # reproject to 3857
                    # I want the final image to be as square not a rectangle
                    src_crs = CRS.from_epsg(4326)
                    dst_crs = CRS.from_epsg(3857)
                    data, _ = warp.reproject(
                        data,
                        src_transform=f.transform,
                        src_crs=src_crs,
                        dst_crs=dst_crs,
                    )
                    bounds = warp.transform_bounds(src_crs, dst_crs, *bounds)

                bands = []
                for i in range(3):
                    band = data[i]
                    # remove the NaN from the analysis
                    h_, bin_ = np.histogram(
                        band[np.isfinite(band)].flatten(), 3000, density=True
                    )

                    cdf = h_.cumsum()  # cumulative distribution function
                    cdf = 3000 * cdf / cdf[-1]  # normalize

                    # use linear interpolation of cdf to find new pixel values
                    band_equalized = np.interp(band.flatten(), bin_[:-1], cdf)
                    band_equalized = band_equalized.reshape(band.shape)

                    bands.append(band_equalized)

                data = np.stack(bands, axis=0)

                data = data / 3000
                data = data.clip(0, 1)
                data = np.transpose(data, [1, 2, 0])

                # create the square polygon
                x_polygon, y_polygon = gdf_squares.loc[index][
                    "geometry"
                ].exterior.coords.xy

                place = cp.getPositionPdf(placement_id, nb_col)
                ax = axes[place[0], place[1]]
                ax.imshow(data, interpolation="nearest", extent=list(bounds))
                ax.plot(
                    x_polygon,
                    y_polygon,
                    color=cp.polygon_color,
                    linewidth=cp.polygon_width,
                )
                ax.set_title(
                    title_list[m][index],
                    x=0.0,
                    y=1.0,
                    fontsize="small",
                    backgroundcolor="white",
                    ha="left",
                )
                ax.axis("off")
                ax.set_aspect("equal", "box")

                # increment the placement image
                placement_id += 1

            # finish the file with empty plots if needed
            while placement_id < nb_line * nb_col:
                place = cp.getPositionPdf(placement_id, nb_col)
                ax = axes[place[0], place[1]]
                ax.axis("off")
                ax.set_aspect("equal", "box")

                placement_id += 1

            # save the page
            pdf.savefig(fig)
            plt.close("all")

        output.update_progress()

    # merge all the pdf files
    output.add_live_msg("merge all pdf files")
    mergedObject = PdfFileMerger()
    for pdf in pdf_tmps:
        mergedObject.append(PdfFileReader(str(pdf), "rb"))
        pdf.unlink()
    mergedObject.write(str(pdf_file))

    # flush the tmp repository
    for file in cp.tmp_dir.glob("*.*"):
        file.unlink()
    # cp.tmp_dir.rmdir() # if I remove the folder I will not be able to relaunch the app without relaunching everything

    output.add_live_msg("PDF output finished", "success")

    return pdf_file
