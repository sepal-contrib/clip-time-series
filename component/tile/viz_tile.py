import json
from pathlib import Path

from sepal_ui import sepalwidgets as sw 
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
        sources = v.Select(
            items=cp.sources, 
            label=cm.viz.sources, 
            v_model=None, 
            multiple=True,
            chips=True
        )
        bands = v.Select(
            items=[*cp.getAvailableBands()], 
            label=cm.viz.bands, 
            v_model=None
        )
        min_year = v.Select(
            class_='mr-5 ml-5', 
            items=[i for i in range(cp.min_start_year, cp.max_end_year+1)], 
            label=cm.viz.start_year, 
            v_model=cp.min_start_year
        )
        max_year = v.Select(
            class_='ml-5 mr-5',
            items=[i for i in range(cp.min_start_year, cp.max_end_year+1)], 
            label=cm.viz.end_year, 
            v_model=cp.max_end_year
        )
        years = v.Layout(
            xs=12, 
            row=True,  
            children=[min_year, max_year]
        )
        square_size = v.Slider(
            step=500, 
            min=cp.min_square, 
            max=cp.max_square, 
            label=cm.viz.square_size, 
            v_model=2000, 
            thumb_label='always', 
            class_='mt-5'
        )
        
        # bind the inputs
        output = sw.Alert() \
            .bind(sources, viz_io, 'sources') \
            .bind(bands, viz_io, 'bands') \
            .bind(min_year, viz_io, 'start_year') \
            .bind(max_year, viz_io, 'end_year') \
            .bind(square_size, viz_io, 'square_size')
        
        # create the tile 
        super().__init__(
            id_ = "viz_widget",
            title = cm.viz.title,
            btn = sw.Btn(cm.viz.btn),
            inputs = [sources, bands, years, square_size],
            output = output
        )
        
        # js behaviour 
        self.btn.on_event('click', self._display_data)  
        
    def _display_data(self, widget, event, data):
    
        # toggle the loading button
        widget.toggle_loading()
        
        # load the input 
        file = json.loads(self.tb_io.json_table)['pathname']
        pts = self.tb_io.pts
        bands = self.viz_io.bands
        sources = self.viz_io.sources
        start = self.viz_io.start_year
        end = self.viz_io.end_year
        square_size = self.viz_io.square_size
        
        # check input
        if not self.output.check_input(file, cm.viz.no_pts): return widget.toggle_loading()
        if not self.output.check_input(bands, cm.viz.no_bands): return widget.toggle_loading()
        if not self.output.check_input(sources, cm.viz.no_sources): return widget.toggle_loading()
        if not self.output.check_input(start, cm.viz.no_start): return widget.toggle_loading()
        if not self.output.check_input(end, cm.viz.no_end): return widget.toggle_loading()
        if not self.output.check_input(square_size, cm.viz.no_square): return widget.toggle_loading()
        if start > end:
            self.output.add_msg(cm.viz.wrong_date, 'error')
            return widget.toggle_loading()
        
        # security when user remove all satellites (sources = [])
        if not len(sources) > 0: 
            self.output.add_msg(cm.viz.no_source, 'error')
            return widget.toggle_loading()
        
        try:
            # generate a sum-up of the inputs
            msg = cs.set_msg(pts, bands, ' & '.join(sources), Path(file).stem, start, end, square_size)
            self.output.add_msg(msg, 'warning')
        
            # change the checked value 
            self.viz_io.check = True
        
        except Exception as e: 
            self.output.add_live_msg(str(e), 'error')
            
        # toggle the loading button
        widget.toggle_loading()
        
        return 