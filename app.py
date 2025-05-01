from flask import Flask, render_template, request, jsonify, url_for, redirect

from utils import get_data, get_train_punctuality

import subprocess

app = Flask(__name__)

data_df, stations, train_names = get_data()

@app.route('/')
def index():
    dropdown_data = {'stations':stations, 'train_names':train_names}
    return render_template(
        'index.html', 
        dropdown_data=dropdown_data,
        message=None
    )

@app.route('/stats', methods=['GET'], strict_slashes=False)
def stats():
    request_data = {
        'train_name': request.args.get('train'),
        'boarding_point': request.args.get('boarding'),
        'deboarding_point': request.args.get('deboarding')
    }

    if not any(request_data.values()):
        return redirect(url_for('index'))

    dropdown_data = {'stations':stations, 'train_names':train_names}
    
    if not all(request_data.values()):
        message = {'error_message': 'Please select train, boarding and deboarding point from the dropdown'}
        return render_template(
            'index.html', 
            dropdown_data=dropdown_data, 
            request_data=request_data, 
            message=message
        )

    is_valid_route, message_delay_chart_json = get_train_punctuality(data_df, request_data)

    if not is_valid_route:
        message = message_delay_chart_json
        return render_template(
            'index.html', 
            dropdown_data=dropdown_data, 
            request_data=request_data, 
            message=message
        )
    
    delay_chart_json = message_delay_chart_json

    return render_template(
        'index.html', 
        dropdown_data=dropdown_data, 
        delay_chart_json=delay_chart_json, 
        request_data=request_data, 
        message=None
    )

@app.route('/get_dropdown_data', methods=['POST'])
def get_dropdown_data():
    req_data = request.get_json()
    dropdown_data_request_type = req_data.get('drop_down_data_request_type')
    current_dropdown_selection = req_data.get('current_dropdown_selection')

    if dropdown_data_request_type == 'station':
        filtered_data = data_df[(data_df['train_name'] == current_dropdown_selection)]['station'].unique().tolist()
    elif dropdown_data_request_type == 'train':
        filtered_data = data_df[(data_df['station'] == current_dropdown_selection)]['train_name'].unique().tolist()

    return jsonify({'dropdown_data': filtered_data})


@app.route("/refresh")
def refresh_data():
    subprocess.run(["bash", "download_data.sh"])
    return "Data refreshed", 200

if __name__ == "__main__":
    app.run()