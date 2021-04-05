from component import parameter as cp

class VizIo:
    
    def __init__(self):
        #input
        self.check = False
        self.sources = None
        self.bands = None
        self.start_year = cp.min_start_year
        self.end_year = cp.max_end_year
        self.square_size = 2000 #in meters