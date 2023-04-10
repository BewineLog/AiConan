aws_db = {
    "user": "{마스터 사용자 이름}",
    "password": "{마스터 암호}",
    "host": "{DB의 엔드포인트}",
    "port": "3306", # Maria DB의 포트
    "database": "{DB에 만들어둔 database 이름}",
    }

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{aws_db['user']}:{aws_db['password']}@{aws_db['host']}:{aws_db['port']}/{aws_db['database']}?charset=utf8"
