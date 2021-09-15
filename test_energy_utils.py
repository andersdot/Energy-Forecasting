import numpy as np
import energy_utils as eu
import pandas as pd 

def test_find_index():
    meta = pd.DataFrame()
    meta['latitude'] = np.linspace(35, 45, 10)
    meta['longitude'] = np.zeros(10) - 150
    lat = 40.5
    lon = -150
    assert eu.find_index(meta, lat, lon) == 5