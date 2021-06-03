import json 


from wand.image import Image 
from wand.color import Color

import ipywidgets as w

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component.message import cm
from component import scripts as cs
from component import widget as cw

class ExportResult(sw.Tile):
    
    def __init__(self):
        
        super().__init__(
            id_ = 'export_widget',
            title = cm.result.title,
            inputs = ['']
        )
        
class ExportData(sw.Tile):
    
    def __init__(self, ex_model, viz_model, tb_model, result_tile):
        
        # gather model
        self.ex_model = ex_model,
        self.viz_model = viz_model
        self.tb_model = tb_model
        
        # gather the result tile
        self.result_tile = result_tile
        
        # create widgets 
        txt = sw.Markdown('  \n'.join(cm.export.txt))
        
        super().__init__(
            id_ = 'export_widget',
            title = cm.export.title, 
            btn = sw.Btn(cm.export.btn),
            alert = cw.CustomAlert(),
            inputs = [txt]
        )
        
        # js behaviour 
        self.btn.on_event('click', self._export_data)
    
    @su.loading_button(debug=True)
    def _export_data(self, widget, event, data):

        # check only validation     
        if not self.alert.check_input(self.viz_model.check, cm.export.no_input): return
        
        # rename variable for the sake of simplified writting 
        file = json.loads(self.tb_model.json_table)['pathname']
        pts = self.tb_model.pts
        bands = self.viz_model.bands
        sources = self.viz_model.sources
        start = self.viz_model.start_year
        end = self.viz_model.end_year
        square_size = self.viz_model.square_size
        image_size = self.viz_model.image_size
        semester = self.viz_model.semester
    
        
        if cs.is_pdf(file, bands, start, end):
            self.alert.add_live_msg('Pdf already exist', 'success')
            return

        # create the vrt from gee images 
        if self.viz_model.driver == 'planet':
            vrt_list, title_list = cs.get_planet_vrt(
                pts, start, end, image_size, 
                file, bands, semester, self.alert
            )
        elif self.viz_model.driver == 'gee':
            vrt_list, title_list = cs.get_gee_vrt(
                pts, start, end, image_size, 
                file, bands, sources, self.alert
            )

        # export as pdf 
        pdf_file = cs.get_pdf(
            file, start, end, image_size, 
            square_size, vrt_list, title_list, bands, pts, 
            self.alert
        )

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
        
        return 
