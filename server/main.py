import json

import numpy as np
import pandas as pd
import pymysql
from flask import Flask, request, jsonify

import config
import os



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
# @app.route('/getData', methods=["POST"])
def send_to_spring():
    # Data => 단일 패킷 data 기준
    data = json.loads(request.get_json())  # get data from front-end and change json to dict
    index, tensor_data = data_transform(data)  # data to tensor

    # This data for Test
    # data = {'index':0,
    #         'Timestamp':99.11,
    #         'id': 8080,
    #         'dlc': 8,
    #         'data1': 1,
    #         'data2': 1,
    #         'data3': 1,
    #         'data4': 1,
    #         'data5': 1,
    #         'data6': 1,
    #         'data7': 1,
    #         'data8': 1,
    #         }

    index, tensor_data = data_transform(data)

    result = model_predict(tensor_data)  # classification using AI

    if result != 0:
        resp = dict()
        resp['index'] = index
        resp['result'] = result

    data['attack'] = 'Spoofing' if result == 1 or 2 else 'Fuzzy' if result == 3 else 'DoS'

    db_res = data_to_db(data)

    if db_res == 'Success':
        app.logger.info('{}번쨰 data 처리 완료.'.format(index))

    # 응답 처리 코드
    return jsonify(json.dumps(resp)), 200


def model_predict(data):
    # model not uploading
    return 1  # if model uploaded, change to model(data)


# if get data file from Spring. it makes data useful to model
def data_transform(data):
    idx = data['index']
    data.pop('index', None)
    df = pd.DataFrame().from_dict(data, orient='index').T  # need to consider index

    return idx, np.array(df)


# make connection with AWS RDS DB
def create_app(test_config=None):
    if test_config:
        app.config.from_object(config)
    else:
        app.config.update(test_config)

    db.init_app(app)


def data_to_db(data):
    app.logger.info('to_db')
    cursor = mysql_conn.cursor()

    # 쿼리문 실행 // 대충 이런 형식으로 쓸 수 있게 dictionary로 데이터 들어옴
    query = "INSERT INTO userTable (Timestamp, id, dlc, data1, data2 ,data3, data4, data5, data6, data7, data8, " \
            "attack) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    result = cursor.execute(query, (
        float(data['Timestamp']), int(data['id']), int(data['dlc']), int(data['data1']), int(data['data2']),
        int(data['data3']), int(data['data4']), int(data['data5']), int(data['data6']), int(data['data7']),
        int(data['data8']), str(data['attack'])))

    # data to db
    mysql_conn.commit()

    return 'Success'  # return 처리 필요


if __name__ == '__main__':
    # create_app().run('0.0.0.0', port=8000, debug=True)
    app.run('0.0.0.0', port=8000, debug=True)
