import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_spectral_energy(frequency, energy, title="Total Swell Energy (All Directions)", color="cyan", max_period=25):
    """
    Plots Total Energy Density vs Frequency without directional filtering.
    """
    period = 1 / frequency
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=period, 
        y=energy, 
        mode='lines', 
        name='Total Energy',
        line=dict(color=color, width=3),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Period (seconds)",
        yaxis_title="Energy Density (m²/Hz)",
        xaxis=dict(range=[0, max_period]),
        template="plotly_dark",
        height=500
    )
    return fig

def plot_filtered_spectrum(frequency, energy, mean_dir, min_dir=280, max_dir=330, max_period=15):
    """
    Plots ONLY rideable energy components based on direction and period.
    """
    period = 1 / frequency
    filtered_energy = energy.copy()
    
    # Direction mask
    if min_dir < max_dir:
        dir_mask = (mean_dir >= min_dir) & (mean_dir <= max_dir)
    else:
        dir_mask = (mean_dir >= min_dir) | (mean_dir <= max_dir)
        
    # Period mask
    period_mask = period <= max_period
    final_mask = dir_mask & period_mask
    filtered_energy[~final_mask] = 0
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=period, 
        y=filtered_energy, 
        mode='lines', 
        name='Rideable Energy',
        line=dict(color="orange", width=3),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title=f"Rideable Energy ({min_dir}°-{max_dir}°, <{max_period}s)",
        xaxis_title="Period (seconds)",
        yaxis_title="Energy Density (m²/Hz)",
        xaxis=dict(range=[0, max_period]),
        template="plotly_dark",
        height=500
    )
    return fig

def plot_polar_direction(frequency, energy, mean_dir, max_period=25):
    """
    Plots energy distribution by direction.
    """
    # Filter out very low energy bins to avoid noise
    mask = energy > (np.max(energy) * 0.05)
    
    filtered_dir = mean_dir[mask]
    filtered_energy = energy[mask]
    filtered_period = 1 / frequency[mask]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=filtered_period,
        theta=filtered_dir,
        mode='markers',
        marker=dict(
            size=filtered_energy * 10, # Increased scale for better visibility
            color=filtered_energy,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Energy")
        ),
        text=[f"Period: {p:.1f}s, Energy: {e:.2f}" for p, e in zip(filtered_period, filtered_energy)],
        name="Swell Components"
    ))

    fig.update_layout(
        title="Swell Direction by Period (Radius=Period, Theta=Direction)",
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=90), # North at top
            radialaxis=dict(range=[0, max_period], title="Period (s)")
        ),
        template="plotly_dark",
        height=600
    )
    return fig

def plot_hs_comparison(history_df):
    """
    Plots Total Hs vs Rideable Hs over time.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=history_df["time"], 
        y=history_df["hs_total"], 
        mode='lines', 
        name='Total Hs',
        line=dict(color='cyan', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=history_df["time"], 
        y=history_df["hs_rideable"], 
        mode='lines', 
        name='Rideable Hs',
        line=dict(color='orange', width=3),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title="Wave Height History (Total vs. Rideable)",
        xaxis_title="Time",
        yaxis_title="Significant Height (m)",
        template="plotly_dark",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_history_ts(history_df, variable="tp"):
    """
    Plots time series of a variable.
    """
    labels = {
        "tp": "Peak Period (s)",
        "dp": "Peak Direction (deg)"
    }
    
    fig = px.line(history_df, x="time", y=variable, title=f"{labels[variable]} History")
    fig.update_layout(template="plotly_dark")
    return fig
