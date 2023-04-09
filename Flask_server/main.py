import flask
from flask import Flask, request, jsonify
import config
from db_connect import db
import mysql

from flask_socketio import SocketIO ,emit

import pandas as pd
import numpy as np
import torch
import tensorflow as tf

app = Flask(__name__)

#bring AI model
model = tf.keras.models.load_model('model path')
model.eval()


#웹 서버 구동하는 곳.
@app.route('/')
def home():
   return 'This is Home!'



#communicate with web
@app.route('/getData', methods= ["POST"])
def send_to_spring():

    #Data => 단일 패킷 data 기준
    idx = data['index']
    data.pop('index',None)
    data = data_transform(request.get_json()) # data to tensor

    result = model_predict(data) #classification using AI

    if result != 0:
          resp = {'index':, 'result': }
          resp['index'] = idx
          resp['result'] = result


    send_data = json.dumps(data,ident = 2) #dictionary array to json

    data['attack'] = 'Spoofing' if result == 1 or 2 else 'Fuzzy' if result == 3 else 'DoS' 
    db_res = data_to_db(pd.DataFrame.to_dict(data))

    if db_res == 'Success':
        app.logger.info('{}번쨰 data 처리 완료.'.format(idx))
    # 응답 처리 코드
    return jsonify(send_data.json()), 200



def model_predict(data):
    #아직 어떤 처리를 해야할지 모르겠음.
    return model(data)


    
#if get data file from Spring. it makes data useful to model
def data_transform(data):
    df = pd.DataFrame.from_dict(data) # need to consider index
    return torch.tensor(df)




#make connection with AWS RDS DB
def create_app(test_config = None):
    app = Flask(__name__)

    if test_config == None:
      app.config.from_object(config)
    else:
      app.config.update(test_config)

    db.init_app(app)


def data_to_db(data):
    cursor = mysql_conn.cursor()

    # 쿼리문 실행 // 대충 이런 형식으로 쓸 수 있게 dictionary로 데이터 들어옴
    query = "INSERT INTO user (Timestamp, CAN ID, DLC, data1, data2 ,data3, data4, data5, data6, data7, data8, attack) VALUES (%f, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %s)" #dataformat은 다음과 같음 
    result = cursor.excute(query, (data['Timestamp'], data['CAN ID'], data['DLC'], data['data1~8'],data['attack']) )

    #data to db
    mysql_conn.commit()

    return 'Success'

if __name__ == '__main__':
    create_app().run('0.0.0.0',port=8000,debug=True)
