
from flask import Flask
from flask_cors import CORS

import numpy as np
import base64
import json

import os
#from yolo.routes import yolo
# from gesture.routes import gest
from web_admin.routes_admin import admin

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
#app.register_blueprint(yolo)

# app.register_blueprint(gest)
app.register_blueprint(admin)
CORS(app)

# 创建必要的目录
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

if __name__ == '__main__':
    logger.info("服务启动中...")
    
    app.run(
        host='0.0.0.0',
        port=9091,
        debug=True,
        threaded=True
    )