from pathlib import Path

import ipyvuetify as v
from natsort import natsorted
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component import scripts as cs
from component import widget as cw
from component.message import cm


class InputTile(sw.Tile):
    def __init__(self, viz_model, tb_model):

        # gather model
        self.viz_model = viz_model
        self.tb_model = tb_model

        # Create alert
        self.alert = sw.Alert()

        # Create the widgets
        self.driver = v.RadioGroup(
            label=cm.viz.driver,
            row=True,
            v_model=self.viz_model.driver,
            children=[
                v.Radio(key=i, label=n, value=n) for i, n in enumerate(cp.drivers)
            ],
        )

        self.w_id = cw.IdSelect()

        self.sources = v.Select(
            items=cp.sources,
            label=cm.viz.sources,
            v_model=[],
            multiple=True,
            chips=True,
        )

        self.planet_key = sw.PasswordField(label=cm.planet.key_label).hide()

        self.bands = v.Select(
            items=[*cp.getAvailableBands()],
            label=cm.viz.bands,
            v_model=self.viz_model.bands,
        )
        self.mosaics = v.Select(
            items=[],
            label=cm.viz.mosaics,
            v_model=[],
            multiple=True,
            chips=True,
            deletable_chips=True,
            dense=True,
        )

        image_size = v.Slider(
            step=500,
            min=cp.min_image,
            max=cp.max_image,
            label=cm.viz.image_size,
            v_model=self.viz_model.image_size,
            thumb_label="always",
            class_="mt-5",
        )

        square_size = v.Slider(
            step=10,
            min=cp.min_square,
            max=cp.max_square,
            label=cm.viz.square_size,
            v_model=self.viz_model.square_size,
            thumb_label="always",
            class_="mt-5",
        )

        # bind the inputs
        (
            self.viz_model.bind(self.sources, "sources")
            .bind(self.planet_key, "planet_key")
            .bind(self.bands, "bands")
            .bind(self.mosaics, "mosaics")
            .bind(self.driver, "driver")
            .bind(image_size, "image_size")
            .bind(square_size, "square_size")
            .bind(self.w_id, "id_list")
        )

        # create the tile
        super().__init__(
            id_="viz_widget",
            title=cm.viz.title,
            btn=sw.Btn(cm.viz.btn),
            inputs=[
                self.driver,
                self.w_id,
                self.sources,
                self.planet_key,
                self.bands,
                self.mosaics,
                image_size,
                square_size,
            ],
            alert=self.alert,
        )

        # set the default driver
        self._on_driver_change(None)

        # js behaviour
        self.mosaics.on_event("blur", self._reorder_mosaics)
        self.sources.observe(self._update_dates, "v_model")
        self.btn.on_event("click", self._display_data)
        self.driver.observe(self._on_driver_change, "v_model")
        self.planet_key.on_event("blur", self._check_key)
        self.tb_model.observe(self._update_points, "raw_geometry")

    @su.switch("loading", on_widgets=["mosaics"])
    def _reorder_mosaics(self, *args):

        # remove the header from the items-list
        items_no_header = [i for i in self.mosaics.items if "header" not in i]

        # pick back the items from the items list
        order_list = [
            i["value"] for i in items_no_header if i["value"] in self.mosaics.v_model
        ]
        order_list.reverse()

        self.mosaics.v_model = order_list

        return self

    @su.switch("disabled", "loading", on_widgets=["planet_key", "mosaics"])
    def _check_key(self, *args):

        # reset everything related to mosaics and password
        self.planet_key.error_messages = None
        self.mosaics.items = []
        self.mosaics.v_model = []

        # exit if value is None
        if not self.planet_key.v_model:
            return

        # check the key and exit if it's not valid
        if not cs.validate_key(self.planet_key.v_model):
            self.planet_key.error_messages = [cm.planet.invalid_key]
            return

        # display the mosaics names
        self.mosaics.items = cs.get_mosaics()

        return

    @su.loading_button()
    def _display_data(self, widget, event, data):

        # load the input
        id_list = self.viz_model.id_list
        driver = self.viz_model.driver
        file = self.tb_model.json_table["pathname"]
        self.tb_model.raw_geometry
        bands = self.viz_model.bands
        sources = self.viz_model.sources
        mosaics = self.viz_model.mosaics
        square_size = self.viz_model.square_size
        image_size = self.viz_model.image_size
        planet_key = self.viz_model.planet_key

        # check input
        if not all(
            [
                self.alert.check_input(id_list, cm.viz.no_id_list),
                self.alert.check_input(driver, cm.viz.no_driver),
                self.alert.check_input(file, cm.viz.no_pts),
                self.alert.check_input(bands, cm.viz.no_bands),
                self.alert.check_input(mosaics, cm.viz.no_mosaics),
                self.alert.check_input(square_size, cm.viz.no_square),
                self.alert.check_input(image_size, cm.viz.no_image),
            ]
        ):
            return

        # test specific to drivers
        if driver == "planet" and not self.alert.check_input(planet_key, cm.viz.no_key):
            return

        if driver == "gee" and not self.alert.check_input(sources, cm.viz.no_sources):
            return

        # filter the points
        self.viz_model.geometry = self.tb_model.raw_geometry.copy()
        if id_list != [cw.IdSelect.ALL]:
            self.viz_model.geometry = self.viz_model.geometry[
                self.viz_model.geometry.id.isin(id_list)
            ]
            self.viz_model.geometry = self.viz_model.geometry.reset_index(drop=True)

        # generate a sum-up of the inputs
        msg = cs.set_msg(
            self.viz_model.geometry,
            bands,
            sources,
            Path(file).stem,
            mosaics,
            image_size,
            square_size,
            driver,
        )

        self.alert.add_msg(msg, "warning")

        # change the checked value
        self.viz_model.check = True

        return

    @su.switch("loading", on_widgets=["mosaics"])
    def _update_dates(self, change):
        """update the available mosaics for the gee driver."""
        # exit if the driver is not GEE or empty sources
        if self.driver.v_model != "gee" or self.sources.v_model == []:
            return

        # get the starting date
        start = None
        end = cp.gee_max_end_year
        if "sentinel" in self.sources.v_model:
            start = cp.gee_min_sentinel_year

        if "landsat" in self.sources.v_model:
            start = cp.gee_min_landsat_year

        self.mosaics.items = [
            {"text": y, "value": y} for y in range(end, start - 1, -1)
        ]
        self.mosaics.v_model = []

        return self

    def _on_driver_change(self, change):
        """adapt the inputs to the requested sources."""
        # get the driver
        driver = self.driver.v_model

        # empty the datas
        self.reset_inputs()

        if driver == "planet":

            # remove source
            su.hide_component(self.sources)

            # display password
            self.planet_key.show()

            # change bands options and select the default rgb
            self.bands.items = [*cp.planet_bands_combo]
            self.bands.v_model = [*cp.planet_bands_combo][0]

            # adapt dates to available data and default to all available
            self.mosaics.items = []
            self.mosaics.v_model = []

        elif driver == "gee":

            # remove password
            self.planet_key.hide()

            # add source and default to landsat
            su.show_component(self.sources)
            self.sources.v_model = [cp.sources[0]]

            # change band options
            self.bands.items = [*cp.getAvailableBands()]
            self.bands.v_model = [*cp.getAvailableBands()][0]

            # adapt dates to available data
            self._update_dates(None)

        return

    def reset_inputs(self):
        """reset all the inputs."""
        self.sources.v_model = []
        self.planet_key.v_model = ""  # I cannot set to None it make bind bugging
        self.bands.v_model = None
        self.mosaics.v_model = []

        return

    def _update_points(self, change):
        """update the available point list when a new point file is selected."""
        if change["new"] is None:
            return

        # set the items values
        self.w_id.set_items(natsorted(self.tb_model.raw_geometry.id.tolist()))

        return self
