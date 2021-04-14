import json 

from sepal_ui import sepalwidgets as sw
from wand.image import Image 
from wand.color import Color
import ipywidgets as w

from component.message import cm
from component import scripts as cs

class ExportResult(sw.Tile):
    
    def __init__(self):
        
        super().__init__(
            id_ = 'export_widget',
            title = cm.result.title,
            inputs = ['']
        )
        
class ExportData(sw.Tile):
    
    def __init__(self, ex_io, viz_io, tb_io, result_tile):
        
        # gather io 
        self.ex_io = ex_io,
        self.viz_io = viz_io
        self.tb_io = tb_io
        
        # gather the result tile
        self.result_tile = result_tile
        
        # create widgets 
        txt = sw.Markdown('  \n'.join(cm.export.txt))
        
        super().__init__(
            id_ = 'export_widget',
            title = cm.export.title, 
            btn = sw.Btn(cm.export.btn),
            output = sw.Alert(),
            inputs = [txt]
        )
        
        # js behaviour 
        self.btn.on_event('click', self._export_data)
        
    def _export_data(self, widget, event, data):
    
        # toggle the loading button
        widget.toggle_loading()
    
        # check only validation     
        if not self.output.check_input(self.viz_io.check, cm.export.no_input): return widget.toggle_loading()
        
        # rename variable for the sake of simplified writting 
        file = json.loads(self.tb_io.json_table)['pathname']
        pts = self.tb_io.pts
        bands = self.viz_io.bands
        sources = self.viz_io.sources
        start = self.viz_io.start_year
        end = self.viz_io.end_year
        square_size = self.viz_io.square_size
        semester = self.viz_io.semester
    
        #try:
        
        if cs.is_pdf(file, bands, start, end):
            self.output.add_live_msg('Pdf already exist', 'success')
            widget.toggle_loading()
            return
        
        # create the vrt from gee images 
        if self.viz_io.driver == 'planet':
            vrt_list, title_list = cs.get_planet_vrt(pts, start, end, square_size, file, bands, semester, self.output)
        elif self.viz_io.driver == 'gee':
            vrt_list, title_list = cs.get_gee_vrt(pts, start, end, square_size, file, bands, sources, self.output)
            
        # export as pdf 
        pdf_file = cs.get_pdf(file, start, end, square_size, vrt_list, title_list, bands, pts, self.output)
    
        # create a download btn
        dwn = sw.DownloadBtn(cm.export.down_btn, path=str(pdf_file))
    
        # create a preview of the first page
        pdf_file = str(pdf_file)
        preview = pdf_file.replace('.pdf', '_preview.png')
            
        with Image(filename=f'{pdf_file}[0]') as img:
            img.background_color = Color("white")
            img.alpha_channel = 'remove'
            img.save(filename=preview)
                
        img_widget = w.Image(value=open(preview, "rb").read())
    
        self.result_tile.set_content([dwn, img_widget])
    
        #except Exception as e: 
        #    self.output.add_live_msg(str(e), 'error')
    
        # toggle the loading button
        widget.toggle_loading()
    
        return 
