import re
import shutil
from pathlib import Path

import ee
import matplotlib.pyplot as plt
import numpy as np
import rasterio as rio
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfMerger
from rasterio import warp
from rasterio.crs import CRS
from rasterio.windows import from_bounds
from unidecode import unidecode
from sepal_ui.scripts.utils import init_ee

from component import parameter as cp
from component import widget as cw

from .utils import min_diagonal

init_ee()

import numpy as np
from skimage import exposure
from skimage import img_as_float

def process_band(band, adjustment_type):
    # Remove NaNs and flatten the array for processing
    valid_pixels = band[~np.isnan(band)].flatten()

    if adjustment_type == "histogram_equalization":
        h, bin_edges = np.histogram(valid_pixels, bins=3000, density=True)
        cdf = h.cumsum()
        cdf_normalized = cdf / cdf[-1]  # Normalize CDF
        return np.interp(band.flatten(), bin_edges[:-1], cdf_normalized).reshape(band.shape)

    elif adjustment_type == "contrast_stretching":
        p2, p98 = np.percentile(valid_pixels, (2, 98))
        return exposure.rescale_intensity(band, in_range=(p2, p98))

    elif adjustment_type == "adaptive_equalization":
        if band.dtype == np.float32 or band.dtype == np.float64:
            if np.min(band) < -1 or np.max(band) > 1:
                band = img_as_float(band)  # Convert image to float and scale to -1 to 1
        else:
            band = img_as_float(band)  # This also scales to 0 to 1
        return exposure.equalize_adapthist(band, clip_limit=0.03)

    elif adjustment_type == "standard_deviation":
        mean = np.mean(valid_pixels)
        std = np.std(valid_pixels)
        return ((band - mean) / std)  # Normalize by standard deviation

    elif adjustment_type == "percent_clip":
        p1, p99 = np.percentile(valid_pixels, (1, 99))
        return np.clip(band, p1, p99)

    elif adjustment_type == "min_max":
        min_val = np.min(valid_pixels)
        max_val = np.max(valid_pixels)
        return (band - min_val) / (max_val - min_val)

    else:
        raise ValueError("Unsupported adjustment type")


# def adjust_contrast(band, type_: Literal["equalization"]):
#     # remove the NaN from the analysis
#     h_, bin_ = np.histogram(band[np.isfinite(band)].flatten(), 3000, density=True)

#     cdf = h_.cumsum()  # cumulative distribution function
#     cdf = 3000 * cdf / cdf[-1]  # normalize

#     # use linear interpolation of cdf to find new pixel values
#     band_equalized = np.interp(band.flatten(), bin_[:-1], cdf)
#     band_equalized = band_equalized.reshape(band.shape)

#     return band_equalized


def is_pdf(file, bands):
    """check if the pdf is already existing, return false if not."""
    # get the filename
    filename = Path(file).stem

    # extract the bands to use them in names
    name_bands = "_".join(bands.split(", "))

    # pdf name
    pdf_file = cp.result_dir / f"{filename}_{name_bands}.pdf"

    print(pdf_file)

    return pdf_file.is_file()


def get_pdf(
    pdf_filepath: Path,
    mosaics: list,
    image_size: int,
    square_size: int,
    vrt_list: dict,
    title_list: dict,
    band_combo,
    geometry,
    output: cw.CustomAlert,
    tmp_dir: str,
    enhance_method: str,
):

    # copy geometry to build the point gdf
    pts = geometry.copy()
    pts.geometry = pts.geometry.centroid

    # build the geometries that will be drawn on the thumbnails
    # can stay in EPSG:3857 as it will be used in this projection
    geoms = geometry.to_crs(3857)
    geoms.geometry = geoms.buffer(square_size / 2, cap_style=3)

    # build the dictionary to use to build the images thumbnails
    size_dict = {}
    for _, r in geometry.to_crs(3857).iterrows():
        size_dict[r.id] = min_diagonal(r.geometry, image_size)

    # create the buffer grid
    buffers = pts.to_crs(3857)
    buffers["geometry"] = buffers.apply(
        lambda r: r.geometry.buffer(size_dict[r.id] / 2, cap_style=3), axis=1
    )
    buffers = buffers.to_crs(4326)

    # get the disposition in col and line
    nb_col, nb_line = cp.get_dims(len(mosaics))

    pdf_tmps = []

    output.reset_progress(len(pts), "Pdf page created")
    for index, r in buffers.iterrows():

        name = re.sub("[^a-zA-Z\\d\\-\\_]", "_", unidecode(str(r.id)))

        pdf_tmp = tmp_dir / f"{pdf_filepath.stem}_tmp_pts_{name}.pdf"
        pdf_tmps.append(pdf_tmp)

        if pdf_tmp.is_file():
            continue

        # create the resulting pdf
        with PdfPages(pdf_tmp) as pdf:

            # the centroid is a point so I can safely take the first coords
            lat, lng = r.geometry.centroid.coords[0]

            page_title = f"Id: {name} (lat:{lat:.5f}, lng:{lng:.5f})"

            fig, axes = plt.subplots(
                nb_line, nb_col, figsize=(11.69, 8.27), dpi=500, constrained_layout=True
            )

            # I reshape by default to avoid a crash
            # if nb_line = 1 the dimension of the table is reduced
            axes = np.array(axes, dtype=object).reshape(nb_line, nb_col)

            fig.suptitle(page_title, fontsize=16, fontweight="bold")

            # display the images in a fig and export it as a pdf page
            placement_id = 0

            for m in mosaics:

                # load the file
                file = vrt_list[m]

                # extract the buffer bounds
                bounds = r.geometry.bounds

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

                    # extract all the value separately, matplotlib uses
                    # a different convention
                    xmin, ymin, xmax, ymax = warp.transform_bounds(
                        src_crs, dst_crs, *bounds
                    )

                bands = []
                for i in range(3):
                    enhanced_band = process_band(data[i], enhance_method)
                    bands.append(enhanced_band)

                data = np.stack(bands, axis=0)

                # data = data / 3000
                # data = data.clip(0, 1)
                data = np.transpose(data, [1, 2, 0])

                # create the square polygon
                x_polygon, y_polygon = geoms.loc[index]["geometry"].exterior.coords.xy

                place = cp.getPositionPdf(placement_id, nb_col)
                ax = axes[place[0], place[1]]
                ax.imshow(
                    data, interpolation="nearest", extent=[xmin, xmax, ymin, ymax]
                )

                ax.plot(
                    x_polygon,
                    y_polygon,
                    color=cp.polygon_colors[band_combo],
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
    merger = PdfMerger()
    for pdf in pdf_tmps:
        merger.append(pdf)
    merger.write(str(pdf_filepath))

    # flush the tmp repository
    shutil.rmtree(cp.tmp_dir)
    cp.tmp_dir.mkdir()

    output.add_live_msg(f"PDF output finished: {pdf_filepath}", "success")

    return pdf_filepath
