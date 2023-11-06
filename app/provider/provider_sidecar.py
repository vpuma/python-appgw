# coding:utf-8
# backend.py
import configparser
import sys
import requests
from flask import Flask, Response, make_response, abort, request
from flask import jsonify
from flask_apscheduler import APScheduler
from app.services.fclogger import log
from app.services.backend import Backend

from flask import Blueprint,render_template
appgw_provider = Blueprint('myappgw_client',__name__)

DEFAULT_BLUEPRINT = [
    (appgw_provider, '/')
]

def config_blueprint(app):
    for blueprint, prefix in DEFAULT_BLUEPRINT:
        app.register_blueprint(blueprint, url_prefix=prefix)

if len(sys.argv) > 2 and sys.argv[0] == "gunicorn":
    config_file = sys.argv[2]
elif len(sys.argv) > 1 and sys.argv[0] == "flask":
    config_file = sys.argv[1]
else:
    config_file = "app/provider/provider_config.ini"
config = configparser.ConfigParser()
config.read(config_file)
gateway_host = config["GATEWAY"]["HOST"]
gateway_port = config["GATEWAY"]["PORT"]
gateway_url = config["GATEWAY"]["URL"]
GATEWAY = f'http://{gateway_host}:{gateway_port}/{gateway_url}'
MAX_TTL = config["BACKEND_CTRL"]["MAX_TTL"]

def update2gw():
    backend.get_cpuload()
    payload = {"service_type": backend.service_type, "host":backend.host, "port": backend.port, "url": backend.url, "cpuload": backend.cpuload}
    try:
        response = requests.post(f"{GATEWAY}/update", json=payload)
        log.debug("# Update response: {}".format(response))
    except:
        log.debug("# Failed to update to GW")  

class SchedulerConfig(object):
    JOBS = [
        {
            'id': 'job_1',
            'func': update2gw,     # 指定运行的函数
            # 'args': (999,),              # 传入函数的参数
            'trigger': 'interval',       # 指定 定时任务的类型
            'seconds': 60                # 运行的间隔时间
        }
    ]
    SCHEDULER_API_ENABLED = True

    
#backend = Backend("aiapp", "localhost", 7000, "aiapp")
backend = Backend(config["BACKEND"]["TYPE"],config["BACKEND"]["VERSION"],config["BACKEND"]["HOST"],config["BACKEND"]["PORT"],config["BACKEND"]["URL"])


@appgw_provider.route('/health', methods=['GET'])
def get_health():      
    return jsonify({"code": 200, "msg": "OK"})

@appgw_provider.route('/aiapp', methods=['POST'])
def aiapp():
    log.debug("# Provider: {}".format(backend))
    return jsonify({"code": 200, "msg": "OK", "provider": f'{backend.host}:{backend.port}:{backend.url}'})


def register2gw():
    log.info("#" * 60)
    log.info("# Registering to GW {}".format(GATEWAY))
    backend.get_cpuload()
    payload = {"service_type": backend.service_type, "service_version": backend.service_version, "host":backend.host, "port": backend.port, "url": backend.url, "cpuload": backend.cpuload}
    try:
        response = requests.post(f"{GATEWAY}/register", json=payload)
        #log.info("# Register response: {}".format(response))
        log.info("# Successfully registered")
        #log.info("# Response content-type: {}".format(response.headers['Content-Type']))
    except:
        log.info("# Failed to register")
    log.info("#" * 60)

def start_provider():
    log.debug("#" * 60)
    log.debug("# Backend started")    
    register2gw()
    update2gw()
 

if __name__=='__main__':
    log.debug("#" * 60)
    log.debug("# Backend started")    
    register2gw()
    update2gw()
    app = Flask(__name__)
    app.debug = True
    app.config.from_object(SchedulerConfig())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(host="0.0.0.0", port=backend.port, use_reloader=False)
    #app.run(host="0.0.0.0", port=7000, use_reloader=False)