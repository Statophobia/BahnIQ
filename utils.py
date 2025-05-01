import pandas as pd
import json

import plotly
import plotly.graph_objs as go

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

def get_train_punctuality(data_df, request_data):

    train_name = request_data['train_name']
    boarding = request_data['boarding_point']
    deboarding = request_data['deboarding_point']

    is_valid_route = True

    if not check_route_validity(data_df, train_name, boarding, deboarding):
        is_valid_route = False
        return is_valid_route, {'error_message': 'Invalid station order for this train'}

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
    fig.update_layout(title='Average Delay by Week', xaxis_title='Week Start', yaxis_title='Avg Delay (min)')

    # Serialize to JSON for Plotly.js
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return is_valid_route, graph_json