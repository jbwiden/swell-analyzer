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

def get_history(ds, hours=24, min_dir=None, max_dir=None, max_period=None):
    """
    Extracts history for the last N hours, including optional filtered Hs.
    """
    try:
        times = pd.to_datetime(ds.waveTime.values)
        now = times[-1]
        cutoff = now - pd.Timedelta(hours=hours)
        
        mask = times > cutoff
        
        # Base history
        history = pd.DataFrame({
            "time": times[mask],
            "hs_total": ds.waveHs.values[mask],
            "tp": ds.waveTp.values[mask],
            "dp": ds.waveDp.values[mask]
        })

        # Calculate Rideable Hs if filters are provided
        if min_dir is not None and max_dir is not None and max_period is not None:
            # Get dimensions
            freqs = ds.waveFrequency.values
            bandwidths = ds.waveBandwidth.values
            
            # Period mask
            period_mask = (1 / freqs) <= max_period
            
            # Get energy and direction data for the history window
            energy_hist = ds.waveEnergyDensity.values[mask]
            
            mean_dir_var = 'waveMeanDirection' if 'waveMeanDirection' in ds.data_vars else 'waveMeanDir'
            dir_hist = ds[mean_dir_var].values[mask]
            
            rideable_hs = []
            for i in range(len(energy_hist)):
                e = energy_hist[i]
                d = dir_hist[i]
                
                # Direction mask for this time step
                if min_dir < max_dir:
                    d_mask = (d >= min_dir) & (d <= max_dir)
                else:
                    d_mask = (d >= min_dir) | (d <= max_dir)
                
                # Combined mask
                final_mask = d_mask & period_mask
                
                # Integrate energy: Hs = 4 * sqrt(sum(E * df))
                filtered_energy_sum = np.sum(e[final_mask] * bandwidths[final_mask])
                hs_val = 4.0 * np.sqrt(filtered_energy_sum)
                rideable_hs.append(hs_val)
                
            history["hs_rideable"] = rideable_hs
        
        return history
    except Exception as e:
        print(f"Error getting history: {e}")
        return pd.DataFrame()
