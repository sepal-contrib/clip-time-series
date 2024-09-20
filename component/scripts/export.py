import re
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfWriter
from sepal_ui.scripts.utils import init_ee
from unidecode import unidecode

from component import parameter as cp
from component import widget as cw

from .utils import enhance_band, get_buffers, get_pdf_path, remove_tmp_dir, reproject

init_ee()


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
    input_file_path: Path,
    mosaics: list,
    image_size: int,
    square_size: int,
    vrt_list: dict,
    title_list: dict,
    band_combo,
    geometry: gpd.GeoDataFrame,
    output: cw.CustomAlert,
    tmp_dir: str,
    enhance_method: str = "min_max",
    sources: list = [],
):
    pdf_filepath = get_pdf_path(
        input_file_path.stem, sources, band_combo, image_size, enhance_method
    )
    # build the geometries that will be drawn on the thumbnails
    # can stay in EPSG:3857 as it will be used in this projection
    geoms = geometry.to_crs(3857)
    geoms.geometry = geoms.buffer(square_size / 2, cap_style=3)

    buffers = get_buffers(geometry, image_size)

    # get the disposition in col and line
    nb_col, nb_line = cp.get_dims(len(mosaics))

    pdf_tmps = []

    output.reset_progress(len(buffers), "Pdf page created")
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

            for mosaic in mosaics:

                # load the file
                file = vrt_list[mosaic]

                # extract the buffer bounds
                bounds = r.geometry.bounds

                data, (xmin, ymin, xmax, ymax) = reproject(file, bounds)

                bands = []
                for i in range(data.shape[0]):
                    enhanced_band = enhance_band(data[i], enhance_method)
                    bands.append(enhanced_band)

                data = np.stack(bands, axis=0)

                if data.shape[0] == 1:
                    # When there is only one band, do not transpose; use a colormap
                    data = (
                        data.squeeze()
                    )  # Remove the single band dimension for display
                    cmap = "viridis"  # Or another appropriate colormap like 'gray', 'RdYlGn', etc.
                else:
                    # For multi-band data, transpose to match (height, width, bands)
                    data = np.transpose(data, [1, 2, 0])
                    cmap = None  # Default, for RGB

                # create the square polygon
                x_polygon, y_polygon = geoms.loc[index]["geometry"].exterior.coords.xy

                place = cp.getPositionPdf(placement_id, nb_col)
                ax = axes[place[0], place[1]]
                ax.imshow(
                    data,
                    interpolation="nearest",
                    extent=[xmin, xmax, ymin, ymax],
                    cmap=cmap,  # Use the defined colormap for single-band images
                )

                ax.plot(
                    x_polygon,
                    y_polygon,
                    color=cp.polygon_colors[band_combo],
                    linewidth=cp.polygon_width,
                )

                ax.set_title(
                    title_list[mosaic][index],
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
    merger = PdfWriter()
    for pdf in pdf_tmps:
        merger.append(pdf)
    merger.write(str(pdf_filepath))

    # flush the tmp repository
    remove_tmp_dir(tmp_dir)

    output.add_live_msg(f"PDF output finished: {pdf_filepath}", "success")

    return pdf_filepath
