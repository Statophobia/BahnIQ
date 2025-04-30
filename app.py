from flask import Flask, render_template, request

from utils import get_data, get_train_punctuality

app = Flask(__name__)

@app.route('/')
def index():
    dropdown_data = {'stations':stations, 'train_names':train_names}
    return render_template('index.html', dropdown_data=dropdown_data)

@app.route('/stats', methods=['GET'])
def stats():
    request_data = {
        'train_name': request.args['train'],
        'boarding_point': request.args['boarding'],
        'deboarding_point': request.args['deboarding']
    }

    delay_chart_json = get_train_punctuality(data_df, request_data)

    dropdown_data = {'stations':stations, 'train_names':train_names}
    return render_template('index.html', dropdown_data=dropdown_data, delay_chart_json=delay_chart_json)

if __name__ == "__main__":
    data_df, stations, train_names = get_data()
    app.run()