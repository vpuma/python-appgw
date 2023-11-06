from flask import Flask
from app.api import config_blueprint
# from app.api import init_db_session
from flask_apscheduler import APScheduler
from app.services.fclogger import log
from app.api.gateway import Config
from app.api.gateway import sys_init

def creat_app():
   
    # 实例化 app
    app = Flask(__name__)

    # 加载配置项
    sys_init()
    app.debug = True
    
    # app.config.from_object(config.get(config))

    # # 加载拓展
    # config_extensions(app)
    # 加载蓝图
    config_blueprint(app)
    ##init_db_session()

    app.config.from_object(Config())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    return app


    

   