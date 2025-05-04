import pandas as pd
import json
from datetime import datetime, timedelta
import plotly
import plotly.graph_objs as go
import numpy as np
import math

def get_data():
    data_df = pd.read_parquet('data/recent_data.parquet')
    stations = data_df['station'].unique().tolist()
    train_names = data_df['train_name'].unique().tolist()

    return data_df, stations, train_names

def check_route_validity(data_df, train_name, boarding, deboarding):
    df = data_df[data_df["train_name"] == train_name].copy()

    if "train_line_ride_id" not in df.columns:
        print("Missing 'train_line_ride_id' column.")
        return False

    # Find the most common ride ID for this train
    most_common_ride_id = (
        df["train_line_ride_id"]
        .dropna()
        .value_counts()
        .idxmax()
    )

    # Filter data to just this ride
    ride_df = df[df["train_line_ride_id"] == most_common_ride_id]
    stations = ride_df.sort_values(by="train_line_station_num")["station"].drop_duplicates().tolist()

    try:
        b_index = stations.index(boarding)
        d_index = stations.index(deboarding)
        return b_index < d_index
    except ValueError:
        return False

def get_delay_by_week_chart(data_df, request_data):

    train_name = request_data['train_name']
    boarding = request_data['boarding_point']
    deboarding = request_data['deboarding_point']

    filtered_df = data_df[
        (data_df.train_name == train_name) & 
        (data_df.station == deboarding)
    ].copy()

    # Compute week start
    filtered_df['week_start'] = filtered_df['time'].dt.to_period('W').apply(lambda r: r.start_time.date())

    # Find the minimum and maximum weeks
    min_week = filtered_df['week_start'].min()

    # Optionally: Find the first date in the DataFrame
    first_date = filtered_df['time'].min().date()

    print(filtered_df['week_start'].max(), min_week, first_date)

    # Exclude the first week if it's incomplete
    # Check if the first date is later than the start of the week
    if first_date > min_week:
        filtered_df = filtered_df[filtered_df['week_start'] != min_week]

    # Compute weekly averages (including the current/last week even if incomplete)
    weekly_avg_df = (
        filtered_df.groupby('week_start')['delay_in_min']
        .mean()
        .astype(float)
        .reset_index(name='average_delay')
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weekly_avg_df['week_start'].tolist(),
        y=weekly_avg_df['average_delay'].tolist(),
        mode='lines+markers',
        name='Avg Delay'
    ))
    fig.update_layout(
        title='Average Delay by Week', xaxis_title='Week Start', yaxis_title='Avg Delay (min)',
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=40)
    )

    # Serialize to JSON for Plotly.js
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graph_json

def get_short_and_long_term_delay_value(data_df, request_data):
    filtered_df = data_df[
        (data_df.train_name == request_data['train_name']) & 
        (data_df.station == request_data['deboarding_point'])
    ].copy()
    today = pd.Timestamp.today()
    date_three_months_ago = today - pd.DateOffset(months=3)
    date_two_weeks_ago = today - timedelta(weeks=2)
    df_3_months_filtered = filtered_df[filtered_df['time'] >= date_three_months_ago]
    df_2_weeks_filtered = filtered_df[filtered_df['time'] >= date_two_weeks_ago]

    avg_delay_3_months = df_3_months_filtered['delay_in_min'].mean()
    avg_delay_2_weeks = df_2_weeks_filtered['delay_in_min'].mean()
    avg_delay_3_months = round(avg_delay_3_months) if not math.isnan(avg_delay_3_months) else float('nan')
    avg_delay_2_weeks = round(avg_delay_2_weeks) if not math.isnan(avg_delay_2_weeks) else float('nan')
    delay = {
        'short_term_delay': avg_delay_2_weeks,
        'long_term_delay': avg_delay_3_months
    }

    return delay

def get_punctuality_chart(data_df, request_data):
    filtered_df = data_df[
        (data_df['train_name'] == request_data['train_name']) & 
        (data_df['station'] == request_data['deboarding_point'])
    ].copy()
    end_date = pd.to_datetime('today')
    start_date = end_date -  pd.DateOffset(months=3)
    df_recent = filtered_df[
        (filtered_df['time'] >= start_date)
    ].copy()
    df_recent['delay_status'] = df_recent['delay_in_min'].apply(lambda x: 'On time' if x < 6 else 'Delay')
    counts = df_recent['delay_status'].value_counts()
    total = counts.sum()
    on_time_percentage = round((counts.get('On time', 0) / total) * 100)
    labels = counts.index.tolist()
    values = counts.values.tolist()
    colors = ['blue', 'orange']
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=colors)
    )])
    fig.update_layout(
        title_text='Percentage of Train On Time in the Last 3 months', 
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    

def get_delay_by_hour(data_df, request_data):
    filtered_df = data_df[
        (data_df.train_name == request_data['train_name']) & 
        (data_df.station == request_data['deboarding_point'])
    ].copy()
    data_df['hour'] = data_df['time'].dt.hour
    delay_by_hour = data_df.groupby('hour')['delay_in_min'].mean()
    delays = np.array(delay_by_hour.values)
    fig = go.Figure(data=[
        go.Bar(
            x=delay_by_hour.index,
            y=delays,
            marker=dict(
                color=delays,
                colorscale='Reds',  
                colorbar=dict(title='Average Delay ')
            ),
            textposition='outside'
        )
    ])
    fig.update_layout(
        title='Average Train Delay by Hour of Day ',
        xaxis_title='Hour of Day',
        yaxis_title='Average Delay ',
        xaxis=dict(tickmode='linear'),
        bargap=0.2
    )
    fig.update_layout(title_text='Percentage of Trains On Time in the Last 2 Weeks', 
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=40)
    )

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graph_json
    
