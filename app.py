import streamlit as st
import pandas as pd
from src.data_fetcher import fetch_latest_swell_data, get_history
from src.plots import plot_spectral_energy, plot_polar_direction, plot_history_ts, plot_filtered_spectrum, plot_hs_comparison
import datetime
import pytz

# --- Configuration & Presets ---
STATIONS = {
    "Santa Cruz / Monterey": {
        "157": "Monterey Bay North Shelf (SC North)",
        "254": "Point Santa Cruz (Steamer Lane)",
        "158": "Cabrillo Point (Monterey)",
        "156": "Point Sur (Offshore Central)",
    },
    "Santa Barbara / Ventura": {
        "261": "Santa Barbara West (Offshore)",
        "107": "Santa Barbara Channel (Anacapa Passage)",
        "111": "Anacapa Passage",
        "071": "Harvest (Pt Conception)",
    },
    "Malibu / LA": {
        "118": "Leo Carrillo Nearshore",
        "105": "Malibu Nearshore",
        "028": "Santa Monica Basin (Offshore)",
    },
    "Northern California": {
        "029": "Point Reyes",
        "142": "San Francisco Bar",
        "168": "Cape Mendocino",
        "094": "Bodega Bay",
    },
    "Hawaii": {
        "187": "Pauwela (Maui North)",
        "098": "Mokapu (Oahu East)",
        "202": "Hanalei (Kauai North)",
        "165": "Barbers Point (Oahu SW)",
    }
}

# Logic for "Rideable" presets based on selection
PRESETS = {
    "157": {"min": 280, "max": 330, "period": 15, "name": "Greyhound to Natural Bridges"},
    "254": {"min": 250, "max": 310, "period": 12, "name": "SC Harbor Run"},
    "118": {"min": 280, "max": 310, "period": 14, "name": "Leo Carrillo to Will Rogers"},
    "107": {"min": 260, "max": 280, "period": 16, "name": "SB to Santa Claus Lane"},
    "187": {"min": 300, "max": 360, "period": 16, "name": "Maliko Run"},
}

st.set_page_config(page_title="Global Swell Spectrum Analyzer", layout="wide")

st.title("🌊 Multi-Region Swell Spectrum Analyzer")
st.markdown("""
Real-time spectral analysis for downwind foiling and surf planning.
*Data provided by CDIP (Scripps Institution of Oceanography).*
""")

# --- Sidebar ---
st.sidebar.header("🌍 Region & Location")
area = st.sidebar.selectbox("Select Area", list(STATIONS.keys()))
location_id = st.sidebar.selectbox("Select Station", list(STATIONS[area].keys()), 
                                  format_func=lambda x: STATIONS[area][x])

# Load presets if available
default_min, default_max, default_tp = 270, 330, 15
preset_info = ""
if location_id in PRESETS:
    p = PRESETS[location_id]
    default_min, default_max, default_tp = p['min'], p['max'], p['period']
    preset_info = f"*(Defaulted for {p['name']})*"

st.sidebar.subheader("🎯 Rideable Window")
st.sidebar.markdown(preset_info)
min_dir = st.sidebar.slider("Min Direction (°)", 0, 360, default_min)
max_dir = st.sidebar.slider("Max Direction (°)", 0, 360, default_max)
max_period = st.sidebar.slider("Max Period (s)", 5, 25, default_tp)

history_hours = st.sidebar.slider("History (hours)", 6, 72, 24)

def localize_time(utc_dt):
    """Converts UTC numpy datetime64 to Local Pacific Time string."""
    utc_dt = pd.to_datetime(utc_dt).replace(tzinfo=pytz.UTC)
    local_tz = pytz.timezone("America/Los_Angeles")
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime("%Y-%m-%d %I:%M %p %Z")

# --- Fetch & Display ---
with st.spinner(f"Fetching data for {STATIONS[area][location_id]}..."):
    data, ds = fetch_latest_swell_data(location_id)

if data:
    # Use the buoy's actual collection time
    buoy_time_local = localize_time(data['time'])
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Significant Height (Hs)", f"{data['hs']:.2f} m")
    col2.metric("Peak Period (Tp)", f"{data['tp']:.1f} s")
    col3.metric("Peak Direction (Dp)", f"{data['dp']:.0f}°")
    col4.metric("Buoy Time (Local)", buoy_time_local)

    # Plots row 1: Current Spectrum
    st.subheader(f"Current Swell Analysis: {STATIONS[area][location_id]}")
    st.info(f"📅 Data Collected by Buoy: {buoy_time_local}")
    
    col_spec1, col_spec2 = st.columns(2)
    with col_spec1:
        # TOTAL Spectrum (No directional filter)
        fig_spec = plot_spectral_energy(data['frequency'], data['energy'], max_period=max_period)
        st.plotly_chart(fig_spec, use_container_width=True)
    
    with col_spec2:
        # RIDEABLE Spectrum (Filtered by direction and period)
        fig_filtered = plot_filtered_spectrum(data['frequency'], data['energy'], data['mean_dir'], min_dir, max_dir, max_period)
        st.plotly_chart(fig_filtered, use_container_width=True)
    
    st.subheader(f"Swell Direction by Period (Radius=Period, Max={max_period}s)")
    fig_polar = plot_polar_direction(data['frequency'], data['energy'], data['mean_dir'], max_period=max_period)
    st.plotly_chart(fig_polar, use_container_width=True)

    # Plots row 2: History
    st.subheader("Historical Trends (UTC)")
    history_df = get_history(ds, hours=history_hours, min_dir=min_dir, max_dir=max_dir, max_period=max_period)
    
    if not history_df.empty:
        # Highlight the Hs comparison
        st.plotly_chart(plot_hs_comparison(history_df), use_container_width=True)
        
        h1, h2 = st.columns(2)
        with h1:
            st.plotly_chart(plot_history_ts(history_df, "tp"), use_container_width=True)
        with h2:
            st.plotly_chart(plot_history_ts(history_df, "dp"), use_container_width=True)
    else:
        st.warning("Could not retrieve historical data.")

else:
    st.error("Failed to connect to CDIP servers. This station might be offline for maintenance.")

st.sidebar.markdown("---")
st.sidebar.write("Created for Downwinders Worldwide")
