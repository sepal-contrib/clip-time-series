from component import parameter as cp

class VizIo:
    
    def __init__(self):
        
        # viz io is initialized with gee default data (full landsat in rgb from 2008 to 2018)
        
        # inputs
        self.driver = cp.drivers[0]
        self.check = False
        self.bands = [*cp.getAvailableBands()][0]
        self.start_year = 2008
        self.end_year = 2018
        self.square_size = 2000 # in meters
        
        # gee related input
        self.sources = [cp.sources[0]]
        
        # planet inputs 
        self.planet_key = None
        