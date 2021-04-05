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
        export_btn.on_event('click', self._export_data)
        
    def start_process(self, widget, event, data):
    
        # toggle the loading button
        widget.toggle_loading()
     
        # load the input
        file = json.loads(tb_io.json_table)['pathname']
        pts = tb_io.pts
        bands = viz_io.bands
        sources = viz_io.sources
        start = viz_io.start_year
        end = viz_io.end_year
        square_size = viz_io.square_size
        check = viz_io.check
    
        # check only validation     
        if not output.check_input(viz_io.check, cm.export.no_input): return widget.toggle_loading()
    
        try:
            # start the exporting process 
            pdf_file = cs.run(
                json.loads(self.tb_io.json_table)['pathname'],
                self.tb_io.pts,
                self.viz_io.bands,
                self.viz_io.sources,
                self.viz_io.start,
                self.viz_io.end,
                self.viz_io.square_size,
                self.output
            )
        
            # create a download btn
            dwn = sw.DownloadBtn(cm.export.down_btn, path=pdf_file)
        
            # create a preview of the first page
            pdf_file = str(pdf_file)
            preview = pdf_file.replace('.pdf', '_preview.png')
            
            with Image(filename=f'{pdf_file}[0]') as img:
                img.background_color = Color("white")
                img.alpha_channel = 'remove'
                img.save(filename=preview)
                
            img_widget = w.Image(value=open(preview, "rb").read())
    
            self.result_tile.set_content([dwn, img_widget])
    
        except Exception as e: 
            output.add_live_msg(str(e), 'error')
    
        # toggle the loading button
        widget.toggle_loading()
    
        return 
