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

# 추가
from keras.models import load_model
import torch
import pickle
from model import Model

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 이진 분류 모델 파일 불러오기
with open('/home/ec2-user/environment/AiConan/model/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)  # Timestamp scaler
with open('/home/ec2-user/environment/AiConan/model/time_scaler.pkl', 'rb') as f:
    time_scaler = pickle.load(f)  # Timestamp scaler

# model_bl = load_model('/home/ec2-user/environment/AiConan/model/Timeseries_binary_classification(LSTM)98.02.h5')  # learning for binary classification
# model_bc = load_model('/home/ec2-user/environment/AiConan/model/Timeseries_binary_classification(CLF)98.02.h5')  # binary classification
model = load_model('/home/ec2-user/environment/AiConan/model/model.h5')

# # 다중 분류 모델 파일 불러오기
# model_mc = torch.load('/home/ec2-user/environment/AiConan/model/model.pth', map_location=torch.device('cpu'))
# model_mc.load_state_dict(torch.load('/home/ec2-user/environment/AiConan/model/model_dict.pth', map_location=torch.device('cpu')))
#
# # for evaluation
#
# model_mc.eval()

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


# communicate with web
@app.route('/api/detection', methods=["POST"])
def detect():
    noa = 0  # # of attack
    data = request.files['file']  # get csv file from web, file name in ['']


    import io
    # csv_data = io.StringIO(data.stream.read().decode("UTF8"))
    csv_data = pd.read_csv(data)
    resp = dict()
    for row in csv_data.values:
    # row: 해당 행의 데이터 (1차원 배열 형식)
        df_row = pd.DataFrame([row], columns=csv_data.columns)
        np_data = data_transform_for_detection(df_row)
        result = model_detection(np_data)  # binary classification using AI 0: normal 1:  attack
        if int(result) >= 1:
            noa += 1
            # response = request.post('http://your-url.com/endpoint', data=row.to_json())
    resp['numberOfAttack'] = noa
    app.logger.info('binary classification success')
    # 응답 처리 코드
    return jsonify(json.dumps(resp)), 200


# maybe 비동기적으로 동작하면서, db로 정보 전송할 것임.
@app.route('/data', methods=["POST"])
def save(data):
    data = pd.read_json(request.get_data(), orient='records')

    idx, timestamp, data = data_transform_for_classification(data)
    result = model_classification(data)  # need to erase np_data timestamp np.delete(np_data,0,axis=1)

    db_data = np.append(data, result)
    db_data = np.append(db_data,timestamp) # @@이거 index 맞춰야해
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
    is_attack = model(data)
    return is_attack  # if model uploaded, change to model(data)


def model_classification(data):
    which_attack = model_mc(data)
    return which_attack


# if get data file from Spring. it makes data useful to model
def data_transform_for_detection(data):

    if 'Unnamed: 0' in data.columns:
        idx = data['Unnamed: 0']
        data.drop(columns='Unnamed: 0', axis = 1)
    data_df = data.reindex(columns=['Timestamp', 'CAN ID', 'DLC', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8', 'Label'])
    data_df = data_df.drop('Label', axis=1)  # 향후 test file을 어떻게 구성할지에 따라 사라질 수도 있음.
    # Timestamp scaling
    timestamp_data = data_df['Timestamp'].values.reshape(-1, 1)
    scaled_timestamp_data = time_scaler.transform(timestamp_data)

    # Data scaling
    cols_to_scale = ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8']
    data_df[cols_to_scale] = scaler.fit_transform(data_df[cols_to_scale])

    # 변환된 데이터를 다시 데이터프레임에 반영
    # data_df = data_df.astype('int')
    data_df['scaled_timestamp'] = scaled_timestamp_data.flatten()

    data_df = data_df.drop(columns='Timestamp', axis=1)
    data_df = data_df.drop(columns='DLC', axis=1)

    data_df = data_df.reindex(
        columns=['scaled_timestamp', 'CAN ID', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])
    # 차원 변환
    data_df = np.expand_dims(data_df, axis=-1)
    data_df = np.reshape(data_df, (data_df.shape[0], 1, data_df.shape[1]))

    return data_df


def data_transform_for_classification(data):
    idx = data['Unnamed: 0']    # index가 필요할 경우
    timestamp = data['Timestamp']

    data_df = data.drop('Label', axis=1)  # 향후 test file을 어떻게 구성할지에 따라 사라질 수도 있음.
    data_df = data_df.drop('Timestamp', axis=1)

    # 차원 변환
    data_df = np.expand_dims(data_df, axis=-1)
    data_df = np.reshape(data_df, (data_df.shape[0], 1, data_df.shape[1]))

    return idx, timestamp, data_df


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