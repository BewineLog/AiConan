import json

import numpy as np
import pandas
import pandas as pd
import pymysql
from flask import Flask, request, jsonify

import config
import os
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# bring AI model
# model = tf.keras.models.load_model('model path')
# model.eval()


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
    return 'This is Home!!'


# communicate with web
# @app.route('/getCsv', methods=["POST"])
def send_to_web():
    data = request.files['file']  # get csv file from web, file name in ['']

    csv_data = csv.reader(data)

    resp = dict()
    for row in csv_data:
        index, np_data = data_transform(row)
        result_bp = model_predict(np_data)  # binary classification using AI

        if result_bp == 0:
            resp[index] = result_bp
            # response = request.post('http://your-url.com/endpoint', data=np_data)
            app.logger.info('binary classification success')
    # 응답 처리 코드
    return jsonify(json.dumps(resp)), 200


# maybe 비동기적으로 동작하면서, db로 정보 전송할 것임.
# @app.route('/getData', methods=["POST"])
def send_to_db(data):
    data = request.get_data()
    data = data.decode('utf-8')
    data = list(data.split(','))

    result_dp = model_clf(data)  # need to erase np_data timestamp np.delete(np_data,0,axis=1)
    db_data = np.append(data, result_dp)
    db_res = data_to_db(db_data)

    if db_res == 'Success':
        app.logger.info('db update success')

    # 응답 처리 코드
    return 200


def model_predict(data):
    # model not uploading
    # 1. scaling
    # 2. model1 -> model2
    # 3. result
    return 1  # if model uploaded, change to model(data)


def model_clf(data):
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


def data_to_db(data):
    # data index -> 0: time stamp 1: ID 2:DLC 3~10:data 11:attack
    app.logger.info('to_db')
    cursor = mysql_conn.cursor()

    # 쿼리문 실행 
    query = "INSERT INTO userTable (dlc, can_net_id, data, timestamp, attack_types_id)" \
            "VALUES (%s, %s, %s, %s, %s)"
    result = cursor.execute(query, (
        str(data[2]), str(data[1]), str(data[3:11]), float(data[0]), int(data[11])))

    # data to db
    mysql_conn.commit()

    return 'Success'  # return 처리 필요


if __name__ == '__main__':
    # create_app().run('0.0.0.0', port=8000, debug=True)
    app.run('0.0.0.0', port=8000, debug=True)
