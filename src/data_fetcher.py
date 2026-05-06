import xarray as xr
import pandas as pd
import numpy as np

CDIP_REALTIME_URL = "https://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/realtime/157p1_rt.nc"

def fetch_latest_swell_data(station_id="157"):
    """
    Fetches the latest swell data from CDIP THREDDS server.
    """
    try:
        # Standard CDIP realtime URL format
        # Station IDs are usually 3 digits, but the file name often adds 'p1'
        clean_id = str(station_id).strip()
        if not clean_id.endswith('p1'):
            url_id = f"{clean_id}p1"
        else:
            url_id = clean_id
            
        url = f"https://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/realtime/{url_id}_rt.nc"
        ds = xr.open_dataset(url)
        
        # Get the latest time index
        latest_idx = -1
        
        # Debug: check available variables
        # print(ds.data_vars)
        
        # Some stations use waveMeanDirection, others might use something else or not have it
        mean_dir_var = 'waveMeanDirection' if 'waveMeanDirection' in ds.data_vars else 'waveMeanDir'
        mean_dir = ds[mean_dir_var].values[latest_idx] if mean_dir_var in ds.data_vars else np.zeros_like(ds.waveFrequency.values)

        data = {
            "time": ds.waveTime.values[latest_idx],
            "hs": float(ds.waveHs.values[latest_idx]),
            "tp": float(ds.waveTp.values[latest_idx]),
            "dp": float(ds.waveDp.values[latest_idx]),
            "energy": ds.waveEnergyDensity.values[latest_idx],
            "frequency": ds.waveFrequency.values,
            "mean_dir": mean_dir
        }
        
        return data, ds
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None

def get_history(ds, hours=24):
    """
    Extracts history for the last N hours.
    """
    try:
        # waveTime is in seconds since 1970-01-01 (typical for CDIP)
        # But xarray usually decodes it to datetime64
        times = pd.to_datetime(ds.waveTime.values)
        now = times[-1]
        cutoff = now - pd.Timedelta(hours=hours)
        
        mask = times > cutoff
        
        history = pd.DataFrame({
            "time": times[mask],
            "hs": ds.waveHs.values[mask],
            "tp": ds.waveTp.values[mask],
            "dp": ds.waveDp.values[mask]
        })
        
        return history
    except Exception as e:
        print(f"Error getting history: {e}")
        return pd.DataFrame()
