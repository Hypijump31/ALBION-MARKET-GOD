import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional
import numpy as np

def create_price_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create an interactive price chart with volume bars.
    
    Args:
        df: DataFrame containing price and volume data
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'timestamp' not in df.columns or 'price' not in df.columns:
        return go.Figure()
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            name="Price",
            line=dict(color='#1f77b4', width=2),
            hovertemplate='%{y:,.0f} silver<extra></extra>'
        )
    )
    
    # Add 7-day moving average
    if len(df) > 7:
        df['ma7'] = df['price'].rolling(window=7, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['ma7'],
                name="7-Day MA",
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                hovertemplate='%{y:,.0f} silver<extra></extra>'
            )
        )
    
    # Add volume bars if available
    if 'item_count' in df.columns:
        # Normalize volume for better visualization
        max_price = df['price'].max()
        max_vol = df['item_count'].max()
        vol_scale = (max_price * 0.5) / max_vol if max_vol > 0 else 0
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['item_count'] * vol_scale,
                name="Volume",
                marker_color='rgba(100, 150, 200, 0.5)',
                yaxis='y2',
                hovertemplate='%{y:,.0f} items<extra></extra>',
                showlegend=False
            )
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Price History",
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Date",
            showgrid=False,
            rangeslider=dict(visible=True)
        ),
        yaxis=dict(
            title="Price (silver)",
            side="left",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis2=dict(
            title="Volume",
            side="right",
            overlaying="y",
            showgrid=False,
            showticklabels=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        plot_bgcolor='white',
        margin=dict(l=50, r=50, t=50, b=50),
        height=500
    )
    
    return fig

def create_market_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap of market activity by day of week and hour.
    
    Args:
        df: DataFrame containing timestamp and item_count
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'timestamp' not in df.columns or 'item_count' not in df.columns:
        return go.Figure()
    
    # Create a copy to avoid modifying the original
    df_heat = df.copy()
    
    # Extract day of week and hour
    df_heat['day_of_week'] = df_heat['timestamp'].dt.day_name()
    df_heat['hour'] = df_heat['timestamp'].dt.hour
    
    # Calculate average volume by day and hour
    heat_data = df_heat.groupby(['day_of_week', 'hour'])['item_count'].mean().reset_index()
    
    # Pivot for heatmap
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heat_pivot = heat_data.pivot(index='day_of_week', columns='hour', values='item_count').reindex(days)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns,
        y=heat_pivot.index,
        colorscale='Viridis',
        colorbar=dict(title='Avg Volume'),
        hovertemplate='Day: %{y}<br>Hour: %{x}:00<br>Avg Volume: %{z:,.0f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Market Activity by Day and Hour",
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Hour of Day (UTC)",
            tickmode='array',
            tickvals=list(range(0, 24, 3))
        ),
        yaxis=dict(
            title="Day of Week"
        ),
        height=500
    )
    
    return fig

def create_price_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Create a histogram of price distribution.
    
    Args:
        df: DataFrame containing price data
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'price' not in df.columns:
        return go.Figure()
    
    fig = px.histogram(
        df,
        x='price',
        nbins=30,
        title="Price Distribution",
        labels={'price': 'Price (silver)'},
        opacity=0.7,
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        height=400
    )
    
    return fig

def create_volume_profile(df: pd.DataFrame, price_bins: int = 20) -> go.Figure:
    """
    Create a volume profile chart showing trading volume at different price levels.
    
    Args:
        df: DataFrame containing price and volume data
        price_bins: Number of price levels to create
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'price' not in df.columns or 'item_count' not in df.columns:
        return go.Figure()
    
    # Create price bins
    min_price = df['price'].min()
    max_price = df['price'].max()
    bin_size = (max_price - min_price) / price_bins
    
    # Assign each trade to a price bin
    df['price_bin'] = ((df['price'] - min_price) / bin_size).astype(int)
    df['price_bin'] = df['price_bin'].clip(0, price_bins-1)
    
    # Calculate total volume per price bin
    volume_profile = df.groupby('price_bin')['item_count'].sum().reset_index()
    volume_profile['price_level'] = min_price + (volume_profile['price_bin'] + 0.5) * bin_size
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=volume_profile['item_count'],
            y=volume_profile['price_level'],
            orientation='h',
            marker_color='#1f77b4',
            hovertemplate='Price: %{y:,.0f}<br>Volume: %{x:,.0f}<extra></extra>'
        )
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Volume Profile",
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Volume",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title="Price Level (silver)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        plot_bgcolor='white',
        height=600,
        margin=dict(l=80, r=20, t=50, b=50)
    )
    
    return fig
