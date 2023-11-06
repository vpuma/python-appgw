# coding:utf-8
from flask import Flask,request,render_template
from flask_apscheduler import APScheduler
# from admin.admin import admin
# from user.user import user
from app.provider.provider_sidecar import appgw_provider
from app.provider.provider_sidecar import config_blueprint
from app.provider.provider_sidecar import SchedulerConfig
from app.services.backend import Backend
from app.provider.provider_sidecar import config, register2gw, update2gw, start_provider

if __name__ == '__main__':
    # 实例化 app
    app = Flask(__name__)
    # 加载配置项
    app.debug = True
    backend = Backend(config["BACKEND"]["TYPE"],config["BACKEND"]["VERSION"],config["BACKEND"]["HOST"],config["BACKEND"]["PORT"],config["BACKEND"]["URL"])
    config_blueprint(app)
    app.config.from_object(SchedulerConfig())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    start_provider()
    app.run(host="0.0.0.0", port=backend.port, use_reloader=False)
