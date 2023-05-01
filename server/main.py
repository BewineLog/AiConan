import json
import datetime
import numpy as np
import pandas
import pandas as pd
import pymysql
from flask import Flask, request, jsonify


import config
import os
import csv

#추가
from keras.models import load_model
import torch
import pickle
from model import Model


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# bring AI model

# 이진 분류 모델 파일 불러오기
with open('path/scaler.pkl', 'rb') as f:
    time_scaler = pickle.load(f)     # Timestamp scaler

model_bl = load_model('path/Timeseries_binary_classification(LSTM)98.02.h5')    # learning for binary classification
model_bc = load_model('path/Timeseries_binary_classification(CLF)98.02.h5')     # binary classification

# 다중 분류 모델 파일 불러오기
state_dict = torch.load('path/lstm_model_acc_99.62.pth')
model_mc = Model()
model_mc.load_state_dict(state_dict["model"])

# for evaluation
model_bl.eval()
model_bc.eval()
model_mc.eval()


mysql_conn = pymysql.connect(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    db=os.environ.get("DB_NAME"),
    port=3306,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)


# 웹 서버 구동하는 곳.
@app.route('/')
def home():
    return 'This is Flask API for AIConan Service!'


import concurrent.futures
import threading

# communicate with web
@app.route('/detection', methods=["POST"])
def detect():
    data = request.files['file']  # get csv file from web, file name in ['']

    csv_data = csv.reader(data)

    resp = dict()
    for row in csv_data:
        index, np_data = data_transform(row)
        result_bp = model_detection(np_data)  # binary classification using AI

        if result_bp == 0:
            resp[index] = result_bp
            # response = request.post('http://your-url.com/endpoint', data=np_data)
            app.logger.info('binary classification success')
    # 응답 처리 코드
    return jsonify(json.dumps(resp)), 200



# maybe 비동기적으로 동작하면서, db로 정보 전송할 것임.
@app.route('/data', methods=["POST"])
def save(data):
    data = request.get_data()
    data = data.decode('utf-8')
    data = list(data.split(','))

    result_dp = model_classification(data)  # need to erase np_data timestamp np.delete(np_data,0,axis=1)
    db_data = np.append(data, result_dp)
    db_res = insert(db_data)

    if db_res == 'Success':
        app.logger.info('db update success')

    # 응답 처리 코드
    return 200


def model_detection(data):
    # model not uploading
    # 1. scaling
    # 2. model1 -> model2
    # 3. result

    # use model model_bl, model_bc


    return 1  # if model uploaded, change to model(data)


def model_classification(data):
    # model(x)
    return 1


# if get data file from Spring. it makes data useful to model
def data_transform(data):
    idx = data[0]
    np_array = np.array(data[1:])
    return idx, np_array


# make connection with AWS RDS DB
# def create_app(test_config=None):
#     if test_config:
#         app.config.from_object(config)
#     else:
#         app.config.update(test_config)
#
#     db.init_app(app)

def insert(data):
    # data is an array of JSON objects, each containing the following keys: 
    # 'timestamp', 'ID', 'DLC', 'data', 'attack'
    app.logger.info('save data to DB')
    cursor = mysql_conn.cursor()

    # Build a list of tuples, each representing a row to be inserted into the database
    rows_to_insert = []
    for row in data:
        # Convert the timestamp value to a datetime object
        timestamp = datetime.datetime.utcfromtimestamp(row['timestamp'])
        # Format the timestamp as a string in the format '%Y-%m-%d %H:%M:%S.%f'
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        row_tuple = (
            str(row['DLC']), 
            str(row['ID']), 
            str(row['data'][0]), 
            str(row['data'][1]), 
            str(row['data'][2]), 
            str(row['data'][3]), 
            str(row['data'][4]), 
            str(row['data'][5]), 
            str(row['data'][6]), 
            str(row['data'][7]), 
            timestamp_str, 
            int(row['attack'])
        )
        rows_to_insert.append(row_tuple)

    # Execute a batch insert query to insert all rows at once
    query = "INSERT INTO abnormal_packets (dlc, can_net_id, data_1, data_2, data_3, data_4, data_5, data_6, data_7, data_8, timestamp, attack_types_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    result = cursor.executemany(query, rows_to_insert)

    # Commit the changes to the database
    mysql_conn.commit()

    return 'Success'



if __name__ == '__main__':
    # create_app().run('0.0.0.0', port=8000, debug=True)
    app.run('0.0.0.0', port=8000, debug=True)
