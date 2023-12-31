import json
import datetime
import numpy as np
import pandas
import pandas as pd
import pymysql
import requests
from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


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
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 이진 분류 모델 파일 불러오기
with open('/home/ec2-user/environment/AiConan/model/data_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)  # data scaler
with open('/home/ec2-user/environment/AiConan/model/timestamp_scaler.pkl', 'rb') as f:
    time_scaler = pickle.load(f)  # Timestamp scaler
model = load_model('/home/ec2-user/environment/AiConan/model/binary_model.h5')

# 다중 분류 모델 파일 불러오기
with open('/home/ec2-user/environment/AiConan/model/data_scaler_mc.pkl', 'rb') as f:
    scaler_mc = pickle.load(f)  # data scaler
with open('/home/ec2-user/environment/AiConan/model/time_scaler_mc.pkl', 'rb') as f:
    time_scaler_mc = pickle.load(f)  # Timestamp scaler

model_mc = load_model('/home/ec2-user/environment/AiConan/model/model.h5')


mysql_conn = pymysql.connect(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    db=os.environ.get("DB_NAME"),
    port=3306,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = mysql_conn.cursor()

app.secret_key = os.environ.get("APP_SECRET_KEY", "default_secret_key")

import secrets
# define authentication endpoint
@app.route('/authenticate', methods=['POST'])
def authenticate():
    userId = request.form['userId']
    password = request.form['password']
    print(f">>> user id : {userId}, user pwd : {password}")
    
    # check if user exists in the database
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

# from flask_sqlalchemy import SQLAlchemy
# # Initialize SQLAlchemy
# db = SQLAlchemy()

# # Define User model
# class User(db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(255), nullable=False)

#     def __init__(self, username):
#         self.username = username

# communicate with web
@app.route('/api/detection', methods=["POST"])
def detect():
    noa = 0  # # of attack
    
    #receive data from web
    data = request.files['file']
    username = request.form['username']
    #  Data preprocessing
    csv_data = pd.read_csv(data) 
    df_row = pd.DataFrame(csv_data, columns=csv_data.columns)

    #   Drop unusable column
    if 'Unnamed: 0' in df_row.columns:
        df_row.drop(columns='Unnamed: 0', axis=1,inplace=True)

    np_data = data_transform_for_detection(df_row)
    resp = dict()
    
    #   Attack detection using AI model
    result = model_detection(np_data)  # binary classification using AI 0: normal 1:  attack
    noa = Counter(result.round().tolist())[1.0]
    resp['numberOfAttack'] = noa
    
    #   Get attack data's index
    index = np.where(result.round() == 1)[0]

    user_id = get_user_id(username)
    print(">> id : ", user_id)
    if len(index) > 0:  # if attack is existed
        json_data = {'index': index, 'origin_data': df_row.iloc[index,:], 'user': username}
        
        save(json_data, user_id)
        
        normal_df = df_row.drop(index)
        insert(normal_df, user_id)

    else:
        insert(df_row, user_id)
    
    app.logger.info('binary classification success')
    # 응답 처리 코드
    return jsonify(json.dumps(resp)), 200

def save(data, user_id):
    if request.is_json:
        data = request.get_json()
        
    np_data = data_transform_for_classification(data['origin_data'])
    result = model_classification(np_data)
    data['origin_data'].loc[:,'Label']= result
    db_res = insert(data['origin_data'], user_id)

    if db_res == 'Success':
        app.logger.info('db update success')

    # 응답 처리 코드
    return 200

def model_detection(data):
    threshold = 0.9634705409763548

    # attack detection using anomaly detection AI model
    res = model(data)
    mse = np.mean(np.power(data - res, 2), axis=1)
    y_pred = np.where(mse > threshold * 0.1, 1, 0)
    is_attack = np.mean(y_pred, axis=1)
    return is_attack


def model_classification(data):
    # classification attack data to detail attack types
    which_attack = model_mc.predict(data)
    return np.argmax(which_attack,axis=1)

def data_transform_for_classification(data):
        
    if 'Label' in data.columns:
        data = data.drop(columns='Label', axis=1)
    data_df = data.reindex(columns=['Timestamp', 'CAN ID', 'DLC', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])


    # Data scaling
    cols_to_scale = ['DLC','Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8']
    data_df[cols_to_scale] = scaler_mc.transform(data_df[cols_to_scale])
    
    # Timestamp scaling
    timestamp = data_df['Timestamp']
    timestamp_data = data_df['Timestamp'].values.reshape(-1, 1)
    scaled_timestamp_data = time_scaler_mc.transform(timestamp_data)
    data_df['scaled_timestamp'] = scaled_timestamp_data.flatten()
    
    # drop Timestamp column and reindexing
    data_df = data_df.drop(columns='Timestamp', axis=1)
    data_df = data_df.reindex(
        columns=['scaled_timestamp', 'CAN ID', 'DLC', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])

    # expand dimension and reshape
    data_df = np.expand_dims(data_df, axis=-1)
    data_df = np.reshape(data_df, (data_df.shape[0], 1, data_df.shape[1]))

    return data_df

# if get data file from Spring. it makes data useful to model
def data_transform_for_detection(data):
        
    if 'Label' in data.columns:
        data = data.drop(columns='Label', axis=1)
        
    data_df = data.reindex(columns=['Timestamp', 'CAN ID', 'DLC', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])

    # Data scaling
    cols_to_scale = ['DLC','Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8']
    data_df[cols_to_scale] = scaler.transform(data_df[cols_to_scale])
    
    # Timestamp scaling
    timestamp = data_df['Timestamp']
    timestamp_data = data_df['Timestamp'].values.reshape(-1, 1)
    scaled_timestamp_data = time_scaler.transform(timestamp_data)
    data_df['scaled_timestamp'] = scaled_timestamp_data.flatten()

    # drop Timestamp column and reindexing
    data_df = data_df.drop(columns='Timestamp', axis=1)
    data_df = data_df.reindex(
        columns=['scaled_timestamp', 'CAN ID', 'DLC', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8'])

    # expand dimension and reshape
    data_df = np.expand_dims(data_df, axis=-1)
    data_df = np.reshape(data_df, (data_df.shape[0], 1, data_df.shape[1]))

    return data_df


# make connection with AWS RDS DB
# def create_app(test_config=None):
#     if test_config:
#         app.config.from_object(config)
#     else:
#         app.config.update(test_config)

#     db.init_app(app)

def insert(data, user_id):
    # data is an array of JSON objects, each containing the following keys: 
    # 'timestamp', 'ID', 'DLC', 'data', 'attack'
    app.logger.info('save data to DB')

    # Build a list of tuples, each representing a row to be inserted into the database
    attack_list = []
    rows_to_insert = []
    for index, row in data.iterrows():


        #time data to 'HH:MM:SS'
        
        current_time = datetime.datetime.now()
        time = row['Timestamp'] / 1000000000
        time_delta = datetime.timedelta(seconds=time)
        new_time = current_time + time_delta
        
        # print(new_time.strftime('%H:%M:%S.%f'))
        data_string =  str(row['Data1']) + str(row['Data2'])+ str(row['Data3'])+ str(row['Data4'])+str(row['Data5'])+\
            str(row['Data6'])+\
            str(row['Data7'])+\
            str(row['Data8'])
        attack_type = 1 if int(row['Label']) == 0 else 2 if int(row['Label']) == 4 else 3 if int(row['Label']) == 3 else 4
        attack_list.append(attack_type)

        row_tuple = (
            str(int(8)),
            str(row['CAN ID']),
            data_string,
            str(new_time.strftime('%H:%M:%S.%f')),
            attack_type,
            user_id
        )
        rows_to_insert.append(row_tuple)
        
    # Execute a batch insert query to insert all rows at once
    query = "INSERT INTO abnormal_packets (dlc, can_net_id, data, timestamp, attack_types_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)"
    result = cursor.executemany(query, rows_to_insert)
    # Commit the changes to the database
    mysql_conn.commit()

    return 'Success'
    
def get_user_id(username):
    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user is None:
            cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
            mysql_conn.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user['id']

    return user_id

@app.route('/api/data', methods=["GET"])
def get_data():
    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM abnormal_packets;")
        data = cursor.fetchall()

    return jsonify(data)
@app.route('/users', methods=['GET'])
def get_users():
    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    return jsonify(users)

@app.route('/data/<int:user_id>', methods=['GET'])
def get_user_data(user_id):
    with mysql_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM abnormal_packets WHERE user_id = %s;", (user_id,))
        data = cursor.fetchall()

    if not data:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(data)

if __name__ == '__main__':
    app.run()