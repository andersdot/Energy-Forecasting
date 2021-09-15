import pandas as pd
import h5pyd
import numpy as np

"""
Utilities for reading in h5py files from NSRDB
"""

def find_index(meta, lat, lon):
    """
    Given a latitude and longitude, 
    find the index of meta with the closest latitude and longitude
    Scales as logN instead of N 
    Input:
        meta - dateframe containing header meta information
        lat - latidute
        lon - longitude
    Return: 
        index -> int    
    """
    from sklearn.neighbors import BallTree

    # Creates new columns converting coordinate degrees to radians.
    for column in ["latitude", "longitude"]:
        rad = np.deg2rad(meta[column].values)
        meta[f'{column}_rad'] = rad

    # convert input latitude and longitude to radians
    rad_lat, rad_lon = np.deg2rad(lat), np.deg2rad(lon)

    #Create balltree using haversine distances
    ball = BallTree(meta[["latitude_rad", "longitude_rad"]].values, metric='haversine')

    #leaf size of 2
    k = 2

    #query tree
    distances, indices = ball.query(np.array([rad_lat, rad_lon]).reshape(1, -1), k=k)

    #return the first index 
    return indices[0][0]



def access_data(columns, f, time_series, index):
    """
    Given a set of columns, 
    extract them from database and add them to time_series
    """ 
    for var in columns:
        # Get dataset
        ds = f[var]
        # Extract scale factor
        scale_factor = ds.attrs['psm_scale_factor']
        # Extract site index and add to DataFrame
        time_series[var] = ds[:, index] / scale_factor
    return time_series

def create_single_timeseries(f, columns, index):
    """
    Given a single file,
    generate a DataFrame with columns and index 
    indexed by time
    """
    time_index = pd.to_datetime(f['time_index'][...].astype(str)).tz_localize(None)
    time_series = pd.DataFrame(index=time_index)
    time_series = access_data(columns, f, time_series, index)
    return time_series



def timeseries(lon=-105, lat=40, years=None, columns=None):
    """
    Given a latitude, longitude, year
    create a DataFrame containing columns for that space-time
    Input:
        lon - longitude [degrees]
        lat - latitude [degrees]
        years - List [int]
        columns - List [str]
    Return: 
        DataFrame
    """
    #set default values
    if columns is None:
        columns = ['ghi', 'air_temperature']
    if years is None:
        years = ['2020']

    #read in first file to access meta data 
    # for finding our position's index in the file 
    f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{years[0]}.h5", 'r')
    meta = pd.DataFrame(f['meta'][...])
    index = find_index(meta, lat, lon)

    #since the file's already read in, let's create it's time_series
    time_series = create_single_timeseries(f, columns, index)
    print(len(time_series))

    #append other years' timeseries
    # !!! this assumes that the meta data is the same for each file
    # true here, and expensive to read, but caution 
    if len(years) > 1:
        for y in years[1:]:
            f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{y}.h5", 'r')
            ts_new = create_single_timeseries(f, columns, index)
            time_series = time_series.append(ts_new)
            print(len(ts_new), len(time_series))
    return meta, time_series