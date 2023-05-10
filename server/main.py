import json
import datetime
import numpy as np
import pandas
import pandas as pd
import pymysql
from flask import Flask, request, jsonify, render_template, redirect, session

import config
import os
import csv

# 추가
from keras.models import load_model
import torch
import pickle
from model import Model

#add
from collections import Counter
import tensorflow as tf

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 이진 분류 모델 파일 불러오기
with open('/home/ec2-user/environment/AiConan/model/binary_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)  # Timestamp scaler
with open('/home/ec2-user/environment/AiConan/model/binary_time_scaler.pkl', 'rb') as f:
    time_scaler = pickle.load(f)  # Timestamp scaler
model = load_model('/home/ec2-user/environment/AiConan/model/binary_model.h5')
model_mc = load_model('/home/ec2-user/environment/AiConan/model/binary_model.h5')


mysql_conn = pymysql.connect(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    db=os.environ.get("DB_NAME"),
    port=3306,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

app.secret_key = os.environ.get("APP_SECRET_KEY", "default_secret_key")

# define login page endpoint
@app.route('/auth')
def login():
    return render_template('login.html')

import secrets
# define authentication endpoint
@app.route('/authenticate', methods=['POST'])
def authenticate():
    userId = request.form['userId']
    password = request.form['password']
    print(f">>> user id : {userId}, user pwd : {password}")
    
    # check if user exists in the database
    cursor = mysql_conn.cursor()
    cursor.execute("SELECT id FROM admin WHERE userId = %s AND password = %s", (userId, password))
    admin = cursor.fetchone()

    # if user exists, create a new authentication token and return it as a JSON response
    import uuid
    if admin is not None:
        token = str(uuid.uuid4())
        session['admin'] = admin['id']
        print(">>> admin login")
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Invalid user ID or password.'}), 401

# define logout endpoint
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return jsonify({'message': 'Logout successful'})

# communicate with web
@app.route('/api/detection', methods=["POST"])
def detect():
    noa = 0  # # of attack

    if request.files.get('file'):   # get csv file for packet data
        data = request.files['file']
    if request.files.get('json_file'):  # get json file for username
        json_file = request.files['json_file']

    #   Data preprocessing
    csv_data = pd.read_csv(data)
    df_row = pd.DataFrame(csv_data, columns=csv_data.columns)
    timestamp, np_data = data_transform_for_detection(df_row)
    resp = dict()

    #   Attack detection using AI model
    result = model_detection(np_data)  # binary classification using AI 0: normal 1:  attack
    noa = Counter(result.round().tolist())[1.0]

    #   Send data to classification model with index, timestamp, data, username
    index = np.where(result.round() == 1)[0]

    json_data = {'index': index, 'origin_data': df_row[index], 'data': np_data[index], 'user': json_file}
    json_data = json.dumps(json_data)

    #   Data 전송 비동기 처리 시, json_data 사용하면 됨.
    resp['numberOfAttack'] = noa
    app.logger.info('binary classification success')
    # 응답 처리 코드
    return jsonify(json.dumps(resp)), 200


# maybe 비동기적으로 동작하면서, db로 정보 전송할 것임.
@app.route('/data', methods=["POST"])
def save(data):
    if request.is_json:
        data = request.get_json()

    print(data['index'])
    print(data['origin_data'])
    print(data['data'])
    print(data['user'])

    result = model_classification(data['data'])  # need to erase np_data timestamp np.delete(np_data,0,axis=1)
    print(Counter(result.round().tolist()))     # for check # of classified attack
    label = pd.DataFrame({'attack': result.tolist()})
    # user = pd.DataFrame({'user': data['user']})
    origin_data = pd.concat([data['origin_data'], label], axis=1)

    print(origin_data)  # for check final data format
    # db_res = insert(origin_data)

    # if db_res == 'Success':
    #     app.logger.info('db update success')

    # 응답 처리 코드
    return 200


def model_detection(data):
    threshold = 1.0556942654891701

    # attack detection using anomaly detection AI model
    res = model(data)
    mse = np.mean(np.power(data - res, 2), axis=1)
    y_pred = np.where(mse > threshold * 0.1, 1, 0)
    is_attack = np.mean(y_pred, axis=1)
    return is_attack


def model_classification(data):
    which_attack = model_mc(data)
    return which_attack


# if get data file from Spring. it makes data useful to model
def data_transform_for_detection(data):

    if 'Unnamed: 0' in data.columns:
        idx = data['Unnamed: 0']
        data = data.drop(columns='Unnamed: 0', axis=1)
    if 'Label' in data.columns:
        data = data.drop(columns='Label', axis=1)
    if 'DLC' in data.columns:
        data = data.drop(columns='DLC', axis=1)
    data_df = data.reindex(columns=['Timestamp', 'CAN ID', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])

    # Timestamp scaling
    timestamp = data_df['Timestamp']
    timestamp_data = data_df['Timestamp'].values.reshape(-1, 1)
    scaled_timestamp_data = time_scaler.transform(timestamp_data)

    # Data scaling
    cols_to_scale = ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8']
    data_df[cols_to_scale] = scaler.fit_transform(data_df[cols_to_scale])

    # 변환된 데이터를 다시 데이터프레임에 반영
    data_df['scaled_timestamp'] = scaled_timestamp_data.flatten()

    data_df = data_df.drop(columns='Timestamp', axis=1)

    data_df = data_df.reindex(
        columns=['scaled_timestamp', 'CAN ID', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])
    # 차원 변환
    data_df = np.expand_dims(data_df, axis=-1)
    data_df = np.reshape(data_df, (data_df.shape[0], 1, data_df.shape[1]))

    return timestamp, data_df


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