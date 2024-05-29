from pathlib import Path
import shutil
import tempfile
import ipywidgets as w
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from traitlets import link
from wand.color import Color
from wand.image import Image

from sepal_ui.planetapi import PlanetModel

from component import scripts as cs
from component import widget as cw
from component.message import cm
from component.parameter.directory import result_dir
from component.scripts.utils import get_pdf_path, get_vrt_filename


class ExportResult(sw.Tile):
    def __init__(self):
        super().__init__(id_="export_widget", title=cm.result.title, inputs=[""])


class ExportData(sw.Tile):
    def __init__(
        self, ex_model, viz_model, tb_model, result_tile, planet_model: PlanetModel
    ):
        # gather model
        self.ex_model = ex_model
        self.viz_model = viz_model
        self.tb_model = tb_model
        self.planet_model = planet_model

        # gather the result tile
        self.result_tile = result_tile

        # create widgets
        txt = sw.Markdown("  \n".join(cm.export.txt))
        w_overwrite = sw.Checkbox(
            label="Overwrite existing file", v_model=ex_model.overwrite
        )

        w_enhanced = sw.Select(
            label="Enhance method",
            items=[
                {"value": "histogram_equalization", "text": "Histogarm equalization"},
                {"value": "contrast_stretching", "text": "Contrast stretching"},
                {"value": "adaptive_equalization", "text": "Adaptive equalization"},
                {"value": "standard_deviation", "text": "Standard deviation"},
                {"value": "percent_clip", "text": "Percent clip"},
                {"value": "min_max", "text": "Min max"},
            ],
        )

        super().__init__(
            id_="export_widget",
            title=cm.export.title,
            btn=sw.Btn(cm.export.btn),
            alert=cw.CustomAlert(),
            inputs=[txt, w_overwrite, w_enhanced],
        )

        # js behaviour
        self.btn.on_event("click", self._export_data)

        link((self.ex_model, "overwrite"), (w_overwrite, "v_model"))
        link((self.ex_model, "enhance_method"), (w_enhanced, "v_model"))

    @su.loading_button()
    def _export_data(self, widget, event, data):
        # check only validation
        if not self.alert.check_input(self.viz_model.check, cm.export.no_input):
            return

        # rename variable for the sake of simplified writting
        file = Path(self.tb_model.json_table["pathname"])
        geometry = self.viz_model.geometry
        bands = self.viz_model.bands
        sources = self.viz_model.sources
        square_size = self.viz_model.square_size
        image_size = self.viz_model.image_size
        mosaics = self.viz_model.mosaics
        enhance_method = self.ex_model.enhance_method

        tmp_dir = Path(tempfile.mkdtemp())
        pdf_filepath = get_pdf_path(
            file.stem, sources, bands, image_size, enhance_method
        )

        try:

            if pdf_filepath.is_file() and not self.ex_model.overwrite:
                self.alert.add_live_msg("Pdf already exist", "success")
                return

            # create the vrt from gee images
            if self.viz_model.driver == "planet":
                vrt_list, title_list = cs.get_planet_vrt(
                    geometry,
                    mosaics,
                    image_size,
                    file.stem,
                    bands,
                    self.alert,
                    tmp_dir,
                    self.planet_model,
                )

            elif self.viz_model.driver == "gee":
                vrt_list, title_list = cs.get_gee_vrt(
                    geometry,
                    mosaics,
                    image_size,
                    file.stem,
                    bands,
                    sources,
                    self.alert,
                    tmp_dir,
                )

            # export as pdf
            pdf_file = cs.get_pdf(
                file,
                mosaics,
                image_size,
                square_size,
                vrt_list,
                title_list,
                bands,
                geometry,
                self.alert,
                tmp_dir,
                enhance_method,
                sources,
            )

            # create a download btn
            dwn = sw.DownloadBtn(cm.export.down_btn, path=str(pdf_file))

            # create a preview of the first page
            pdf_file = str(pdf_file)
            preview = pdf_file.replace(".pdf", "_preview.png")

            with Image(filename=f"{pdf_file}[0]") as img:
                img.background_color = Color("white")
                img.alpha_channel = "remove"
                img.save(filename=preview)

            img_widget = w.Image(value=open(preview, "rb").read())

            self.result_tile.set_content([dwn, img_widget])

        except Exception as e:
            raise e

        finally:
            # remove the temporary folder in any case
            shutil.rmtree(tmp_dir)

        return
