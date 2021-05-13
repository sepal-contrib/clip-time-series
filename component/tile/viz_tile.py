import json
from pathlib import Path

from sepal_ui import sepalwidgets as sw 
from sepal_ui.scripts import utils as su
import ipyvuetify as v

from component.message import cm
from component import parameter as cp
from component import scripts as cs

class InputTile(sw.Tile):
    
    def __init__(self, viz_io, tb_io):
        
        # gather ios 
        self.viz_io = viz_io
        self.tb_io = tb_io
        
        # create the widgets
        self.driver = v.RadioGroup(
            label = cm.viz.driver,
            row= True,
            v_model = self.viz_io.driver,
            children = [v.Radio(key=i, label=n, value=n) for i, n in enumerate(cp.drivers)]
        )
        
        self.sources = v.Select(
            items=cp.sources, 
            label=cm.viz.sources, 
            v_model=self.viz_io.sources, 
            multiple=True,
            chips=True
        )
        
        self.planet_key = sw.PasswordField(label = cm.planet.key_label).hide()
        self.semester = v.RadioGroup(
            label = cm.viz.semester,
            row= True,
            v_model = None,
            children = [v.Radio(label=cp.planet_semesters[n], value=n) for n in [*cp.planet_date_ranges[cp.planet_min_start_year]]]
        )
        su.hide_component(self.semester)
        
        self.bands = v.Select(
            items=[*cp.getAvailableBands()], 
            label=cm.viz.bands, 
            v_model=self.viz_io.bands
        )
        self.start = v.Select(
            class_='mr-5 ml-5', 
            items=[y for y in range(cp.gee_min_start_year, cp.gee_max_end_year+1)], 
            label=cm.viz.start_year, 
            v_model=self.viz_io.start_year
        )
        self.end = v.Select(
            class_='ml-5 mr-5',
            items=[y for y in range(cp.gee_min_start_year, cp.gee_max_end_year+1)], 
            label=cm.viz.end_year, 
            v_model=self.viz_io.end_year
        )
        years = v.Layout(
            xs=12, 
            row=True,  
            children=[self.start, self.end]
        )
        
        image_size = v.Slider(
            step=500, 
            min=cp.min_image, 
            max=cp.max_image, 
            label=cm.viz.image_size, 
            v_model=self.viz_io.image_size, 
            thumb_label='always', 
            class_='mt-5'
        )
        
        square_size = v.Slider(
            step=10, 
            min=cp.min_square, 
            max=cp.max_square, 
            label=cm.viz.square_size, 
            v_model=self.viz_io.square_size, 
            thumb_label='always', 
            class_='mt-5'
        )
        
        
        
        # bind the inputs
        output = sw.Alert() \
            .bind(self.sources, viz_io, 'sources') \
            .bind(self.planet_key, viz_io, 'planet_key', secret = True) \
            .bind(self.bands, viz_io, 'bands') \
            .bind(self.start, viz_io, 'start_year') \
            .bind(self.end, viz_io, 'end_year') \
            .bind(self.driver, viz_io, 'driver') \
            .bind(image_size, viz_io, 'image_size') \
            .bind(square_size, viz_io, 'square_size') \
            .bind(self.semester, viz_io, 'semester')
        
        # create the tile 
        super().__init__(
            id_ = "viz_widget",
            title = cm.viz.title,
            btn = sw.Btn(cm.viz.btn),
            inputs = [self.driver, self.sources, self.planet_key, self.bands, years, self.semester, image_size, square_size],
            output = output
        )
        
        # js behaviour 
        self.btn.on_event('click', self._display_data) 
        self.driver.observe(self._on_driver_change, 'v_model')
        
    def _display_data(self, widget, event, data):
    
        # toggle the loading button
        widget.toggle_loading()
        
        # load the input 
        driver = self.viz_io.driver
        file = json.loads(self.tb_io.json_table)['pathname']
        pts = self.tb_io.pts
        bands = self.viz_io.bands
        sources = self.viz_io.sources
        start = self.viz_io.start_year
        end = self.viz_io.end_year
        square_size = self.viz_io.square_size
        image_size = self.viz_io.image_size
        planet_key = self.viz_io.planet_key
        semester = self.viz_io.semester
        
        # check input
        if not self.output.check_input(driver, cm.viz.no_driver): return widget.toggle_loading()
        if not self.output.check_input(file, cm.viz.no_pts): return widget.toggle_loading()
        if not self.output.check_input(bands, cm.viz.no_bands): return widget.toggle_loading()
        if not self.output.check_input(start, cm.viz.no_start): return widget.toggle_loading()
        if not self.output.check_input(end, cm.viz.no_end): return widget.toggle_loading()
        if not self.output.check_input(square_size, cm.viz.no_square): return widget.toggle_loading()
        if not self.output.check_input(image_size, cm.viz.no_image): return widget.toggle_loading()
        if start > end:
            self.output.add_msg(cm.viz.wrong_date, 'error')
            return widget.toggle_loading()
        
        # test specific to drivers
        if driver == 'planet':
            if not self.output.check_input(planet_key, cm.viz.no_key): return widget.toggle_loading()
            if not self.output.check_input(semester, cm.viz.no_semester): return widget.toggle_loading()
        elif driver == 'gee':
            if not self.output.check_input(sources, cm.viz.no_sources): return widget.toggle_loading()
        
        try:
            if driver == 'planet':
                cs.validate_key(planet_key, self.output)
            
            # generate a sum-up of the inputs
            msg = cs.set_msg(pts, bands, sources, Path(file).stem, start, end, image_size, square_size, driver)
            self.output.add_msg(msg, 'warning')
        
            # change the checked value 
            self.viz_io.check = True
        
        except Exception as e: 
            self.output.add_live_msg(str(e), 'error')
            
        # toggle the loading button
        widget.toggle_loading()
        
        return 
    
    def _on_driver_change(self, change):
        """adapt the inputs to the requested sources"""
        
        # empty the datas 
        self.reset_inputs()
        
        if change['new'] == 'planet':
            # remove source
            su.hide_component(self.sources)
            
            # display password
            self.planet_key.show()
            
            # display semesters 
            su.show_component(self.semester)
            self.semester.v_model = 'S1'
            
            # change bands options and select the default rgb
            self.bands.items = [*cp.planet_bands_combo]
            self.bands.v_model = [*cp.planet_bands_combo][0]
            
            # adapt dates to available data and default to all available
            self.start.items = [y for y in range(cp.planet_min_start_year, cp.planet_max_end_year+1)]
            self.start.v_model = cp.planet_min_start_year
            self.end.items = [y for y in range(cp.planet_min_start_year, cp.planet_max_end_year+1)]
            self.end.v_model = cp.planet_max_end_year
            
        elif change['new'] == 'gee':
            # remove password 
            self.planet_key.hide()
            
            # remove semester 
            su.hide_component(self.semester)
            
            # add source and default to landsat
            su.show_component(self.sources)
            self.sources.v_model = [cp.sources[0]]
            
            # change band options
            self.bands.items = [*cp.getAvailableBands()]
            self.bands.v_model = [*cp.getAvailableBands()][0]
            
            # adapt dates to available data
            self.start.items = [y for y in range(cp.gee_min_start_year, cp.gee_max_end_year+1)]
            self.start.v_model = 2005
            self.end.items = [y for y in range(cp.gee_min_start_year, cp.gee_max_end_year+1)]
            self.end.v_model = 2018
            
        return
        
    def reset_inputs(self):
        """reset all the inputs"""
        
        self.sources.v_model = None
        self.planet_key.v_model = '' # I cannot set to None it make bind bugging
        self.bands.v_model = None
        self.start.v_model = None
        self.end.v_model = None
        self.semester.v_model = None
        
        return 
        
        