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
        #title='Average Delay by Week', 
        xaxis_title='Week', yaxis_title='Avg Delay (min)',
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
    today = pd.Timestamp.today()    
    start_date = today - pd.DateOffset(months=3)
    df_recent = filtered_df[
        (filtered_df['time'] >= start_date)
    ].copy()
    df_recent['delay_status'] = df_recent['delay_in_min'].apply(lambda x: 'On time' if x < 6 else 'Delay')
    counts = df_recent['delay_status'].value_counts()
    total = counts.sum()
    on_time_percentage = round((counts.get('On time', 0) / total) * 100)
    labels = counts.index.tolist()
    values = counts.values.tolist()
    colors = ['red', 'green']
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=colors)
    )])
    fig.update_layout(
        #title_text='Percentage of Train On Time in the Last 3 months', 
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return on_time_percentage, graph_json  


def get_delay_by_hour(data_df, request_data):
    filtered_df = data_df[
    (data_df.station == request_data['deboarding_point'])
    ].copy()
    
    filtered_df['hour'] = filtered_df['time'].dt.hour

    bins = [0, 3, 7, 11, 15, 19, 24]
    labels = ['Mid Night (0-3)', 'Early Morning (4-7)', 'Morning (8-11)', 'Afternoon (12-15)', 'Evening (16-19)', 'Night (20-23)']

    filtered_df['time_category'] = pd.cut(
        filtered_df['hour'],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True
    )
    delay_by_hour = filtered_df.groupby('hour')['delay_in_min'].mean().reindex(range(24), fill_value=0)
    delay_by_category = filtered_df.groupby('time_category')['delay_in_min'].mean()
    category_with_max_delays = delay_by_category.idxmax()
    max_delay = int(round(delay_by_category.max(), 0))
    fig = go.Figure(data=[ 
        go.Bar(
            x=list(range(24)),
            y=delay_by_hour.values.tolist(),
            marker=dict(
                color=delay_by_hour.values.tolist(),
                colorscale=[[0, 'lightcoral'], [1, 'darkred']],
                colorbar=dict(title='Average Delay')
            ),
            textposition='outside'
        )
    ])

    fig.update_layout(
        #title='Average Train Delay by Time of Day',
        xaxis_title='Hour',
        yaxis_title='Average Delay',
        xaxis=dict(
            tickmode='array',
            tickvals=bins[:-1],  # Using the bin values for ticks (e.g., 0, 3, 7, 11, 15, 19)
            ticktext=[str(x) for x in bins[:-1]],  # Use the bin values as tick labels
            tickangle=0
        ),
        bargap=0.2,
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=40)
    )

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return category_with_max_delays, max_delay, graph_json

import plotly.graph_objects as go

def get_alternative_trains_with_delays(data_df, request_data):
    boarding = request_data['boarding_point']
    deboarding = request_data['deboarding_point']
    current_train = request_data['train_name']

    # Filter for trains that stop at both stations
    station_filter = data_df[data_df["station"].isin([boarding, deboarding])]
    trains_with_both = (
        station_filter.groupby("train_name")["station"]
        .nunique()
        .loc[lambda x: x == 2]
        .index
    )

    alternative_trains = []
    
    for train in trains_with_both:
        if train == current_train:
            continue
        if check_route_validity(data_df, train, boarding, deboarding):
            delay_df = data_df[
                (data_df['train_name'] == train) &
                (data_df['station'].isin([boarding, deboarding]))
            ]
            avg_delay = delay_df['delay_in_min'].mean()
            alternative_trains.append((train, round(avg_delay, 1)))

    # Plotting
    if not alternative_trains:
        return None, None, None
    
    alternative_trains = sorted(alternative_trains, key=lambda x: x[1])[:5]
    least_delay_train = alternative_trains[0][0]
    least_delay_value = round(alternative_trains[0][1])

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=["Alternative Trains", "Average Delay"],
                    fill_color="lightgrey",
                    align="left",
                    line_color='black',
                    height=40
                    ),
                cells=dict(
                    values=[
                        [t[0] for t in alternative_trains],
                        [t[1] for t in alternative_trains]
                    ],
                    fill_color="white",
                    align="left",
                    line_color='black',
                    height=40
                )
            )
        ]
    )
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return least_delay_train, least_delay_value, graph_json

def get_delays_by_week(data_df, request_data):
    today = pd.to_datetime('today')
    three_months_ago = today - pd.DateOffset(months=3)
    data_df['day_of_week'] = data_df['time'].dt.day_name()
    df_3_months_filtered = data_df[data_df['time'] >= three_months_ago]
    train_name = request_data['train_name']
    deboarding_station = request_data['deboarding_point']
    filtered_df = df_3_months_filtered[
        (df_3_months_filtered.train_name == train_name) 
    ].copy()
    delays_by_day = filtered_df.groupby('day_of_week').agg (
        average_delay = ('delay_in_min','mean'),
        on_time_percentage = ('delay_in_min', lambda x: (x <= 5).mean() * 100)).reset_index()
    
    max_delay = delays_by_day['average_delay'].max()
    min_delay = delays_by_day['average_delay'].min()

    max_delay_row = delays_by_day[delays_by_day['average_delay'] == max_delay].iloc[0]
    min_delay_row = delays_by_day[delays_by_day['average_delay'] == min_delay].iloc[0]
    max_delay_of_train = round(max_delay)
    min_delay_of_train = round(min_delay)
    max_delay_day = max_delay_row['day_of_week']
    min_delay_day = min_delay_row['day_of_week']

    deboarding_df = df_3_months_filtered.groupby('day_of_week').agg(
        deboarding_avg_Delay = ('delay_in_min','mean')).reset_index()
    combined_stats = pd.merge(deboarding_df, delays_by_day, on='day_of_week', how='outer')

    week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    combined_stats['day_of_week'] = pd.Categorical(combined_stats['day_of_week'], categories=week_order, ordered=True)
    combined_stats = combined_stats.sort_values('day_of_week')

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[
                "<b>Days</b>",
                "<b>Avg. delay of train</b>",
                "<b>Punctuality rate of train(%)</b>",
                "<b>Avg. delay of all trains at deboarding station</b>"
            ],
            fill_color='lightskyblue',
            align='left',
            font=dict(size=14, color='black'),
            height=40
        ),
        cells=dict(
            values=[
                combined_stats['day_of_week'],
                combined_stats['average_delay'].round(2),
                combined_stats['on_time_percentage'].round(1),
                combined_stats['deboarding_avg_Delay'].round(2)
            ],
            fill_color='aliceblue',
            align='left',
            font=dict(size=13),
            height=40
        )
    )])

    fig.update_layout(
        #title="Delay Statistics by Day",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return max_delay_of_train, min_delay_of_train, max_delay_day, min_delay_day, graph_json

  