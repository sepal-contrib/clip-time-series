import tempfile
from pathlib import Path

import ipywidgets as w
from sepal_ui import sepalwidgets as sw
from sepal_ui.planetapi import PlanetModel
from sepal_ui.scripts import utils as su
from traitlets import link
from wand.color import Color
from wand.image import Image

from component import scripts as cs
from component import widget as cw
from component.message import cm
from component.scripts.task_controller import TaskController
from component.scripts.utils import get_pdf_path, remove_tmp_dir


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
        self.stop_btn = sw.Btn(
            text="Stop", small=True, class_="ml-2", color="secondary    "
        )
        self.set_children(self.stop_btn, "last")
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

        def process(shared_variable):
            # create the vrt from gee images
            if self.viz_model.driver == "planet":
                vrt_list, title_list = cs.get_planet_vrt(
                    geometry=geometry,
                    mosaics=mosaics,
                    image_size=image_size,
                    filename=file.stem,
                    bands=bands,
                    out=self.alert,
                    tmp_dir=tmp_dir,
                    planet_model=self.planet_model,
                    shared_variable=shared_variable,
                )

            elif self.viz_model.driver == "gee":
                vrt_list, title_list = cs.get_gee_vrt(
                    geometry=geometry,
                    mosaics=mosaics,
                    image_size=image_size,
                    filename=file.stem,
                    bands=bands,
                    sources=sources,
                    output=self.alert,
                    tmp_dir=tmp_dir,
                    shared_variable=shared_variable,
                )

            # export as pdf
            pdf_file = cs.get_pdf(
                input_file_path=file,
                mosaics=mosaics,
                image_size=image_size,
                square_size=square_size,
                vrt_list=vrt_list,
                title_list=title_list,
                band_combo=bands,
                geometry=geometry,
                output=self.alert,
                tmp_dir=tmp_dir,
                enhance_method=enhance_method,
                sources=sources,
                shared_variable=shared_variable,
            )

            return pdf_file

        def on_task_complete(pdf_file):
            try:
                # create a download button
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
                self.alert.append_msg(f"Error in callback: {e}", type_="error")
                raise e
            finally:
                # remove the temporary folder
                remove_tmp_dir(tmp_dir)

        try:
            if pdf_filepath.is_file() and not self.ex_model.overwrite:
                self.alert.add_live_msg("Pdf already exists", "success")
                return

            # Start the task with the callback
            task_controller = TaskController(
                self.btn,
                self.stop_btn,
                self.alert,
                function=process,
                callback=on_task_complete,
            )
            task_controller.start_task()

        except Exception as e:
            raise e
