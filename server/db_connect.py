from flask_sqlalchemy import SQLAlchemy
from flask import _app_ctx_stack
from flask_cors import CORS

db = SQLAlchemy() #for db
CORS(db)