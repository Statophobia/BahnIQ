import pandas as pd
import json

import plotly
import plotly.graph_objs as go

def get_data():
    data_df = pd.read_parquet('data/recent_data.parquet')
    stations = data_df['station'].unique().tolist()
    train_names = data_df['train_name'].unique().tolist()

    return data_df, stations, train_names

def get_train_punctuality(data_df, request_data):
    filtered_df = data_df[
        (data_df.train_name == request_data['train_name']) & 
        (data_df.station == request_data['deboarding_point'])
    ].copy()

    filtered_df['week_start'] = filtered_df['time'].dt.to_period('W').apply(lambda r: r.start_time.date())
    weekly_avg_df = filtered_df.groupby(['week_start'])['delay_in_min'].mean().astype(float).reset_index(name='average_delay')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weekly_avg_df['week_start'].tolist(),
        y=weekly_avg_df['average_delay'].tolist(),
        mode='lines+markers',
        name='Avg Delay'
    ))
    fig.update_layout(title='Average Delay by Week', xaxis_title='Week Start', yaxis_title='Avg Delay (min)')

    # Serialize to JSON for Plotly.js
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graph_json