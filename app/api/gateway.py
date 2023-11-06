# gateway.py
# curl -H "Content-Type: application/json" -X POST -d '{"action":"CREATE", "name":"test0017"}' http://localhost:5000/aiapp && echo ""

# curl -H "Content-Type: application/json" -X POST -d '{"callback_url": "http://v.dt01.vtc365.cn/LiveVideoServer/ajx/ai_post.do", "action": "PR_CREATE", "url": "http://v3.test01.vtclive.com/LiveVideoServer/streams/s42/4025/99335/live.m3u8", "version": 1, "name": "nlt01.vtc365.com_4025_99335", "randomStr": "a8alm78Jw1v2Aba6cArD", "ppt": "no", "face": "yes"}' http://localhost:5000/gw/aiapp && echo ""


import sys
import configparser
import requests
from flask import Flask, Response, make_response, abort, request, jsonify
import json
from flask_apscheduler import APScheduler
from app.services.fclogger import log
from app.services.backend import Backend
from app.models.models import Provider
from app.models.models import Service
from app.models.models import Task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
from .config import init_config, init_db_session
from app.daos.daos import query_service_type, add_provider, query_provider, update_provider, query_active_providers, query_valid_services, query_all_providers, query_ongoing_tasks
# from app.api import config_blueprint
# import time

# ------------------------------- Init ----------------------------
# init backend control variables
config = init_config()
DBSession = init_db_session(config)

HEARTBEAT_INTERVAL = int(config['BACKEND_CTRL']['HEARTBEAT_INTERVAL'])
MAX_TTL = int(config['BACKEND_CTRL']['MAX_TTL'])
CPU_LOAD_THRESHOLD = int(config['BACKEND_CTRL']['CPU_LOAD_THRESHOLD'])
# backend variables
g_backends = [] # backends['aiapp'][#]
g_service_types = []
g_backends_map = {}
g_round_robin = 0

from flask import Blueprint
gw = Blueprint('mygateway', __name__)

# Check the health status of all providers, every 10 seconds
def check_providers():      
    # session = DBSession()
    log.debug("#" * 40)
    log.debug("# Checking providers ...")
    # providers = session.query(Provider).filter(Provider.active == 1).all()
    providers = query_active_providers()
    if providers is None:
        log.warn("# No active providers")
        return
    for provider in providers:
        log.debug("# Checking {}:{}:{} active={} TTL={}".format(provider.host, provider.port, provider.path, provider.active, provider.ttl))
        try:
            requests.get(f"http://{provider.host}:{provider.port}/health")                        
        except:
            log.debug("# provider {}:{}:{} is not responding".format(provider.host, provider.port, provider.path))  
            if provider.ttl > 0:    
                provider.ttl -= 1
            if provider.ttl <= 0:
                provider.active = False
            # session.commit()
            update_provider(provider.type, provider.host, provider.port, provider.active, provider.ttl)
            #update_provider()
        else:
            log.debug("# provider {}:{}:{} is active".format(provider.host, provider.port, provider.path))            
    # session.close()
    return

def print_stat():
    log.info("#" * 60)
    log.info("# Backend status:")
    for backend in g_backends:
        if backend.active:
            log.info("# {}:{}:{} is ACTIVE, CPU_load {}%".format(backend.service_type, backend.host, backend.port, backend.cpuload))
        else:
            log.info("# {}:{}:{} is INactive".format(backend.service_type, backend.host, backend.port))
    log.info("# Running tasks:")
    for key, value in g_backends_map.items():
        log.info("# Task:{} -- {}".format(key, value))
    log.info("#" * 60)

###############################################################################
#  define scheduled tasks
class Config(object):
    JOBS = [
        {
            'id': 'job_1',
            'func': check_providers,     # 指定运行的函数
            #'args': (999,),              # 传入函数的参数
            'trigger': 'interval',       # 指定 定时任务的类型
            'seconds': 10                # 运行的间隔时间
        },
        {
            'id': 'job_2',
            'func': print_stat,     # 指定运行的函数
            #'args': (999,),              # 传入函数的参数
            'trigger': 'interval',       # 指定 定时任务的类型
            'seconds': 60                # 运行的间隔时间
        }
    ]
    SCHEDULER_API_ENABLED = True


###############################################################################
## Flask test page
@gw.route('/gw/hello/')
def index():
    return 'this gw server is running on port:5000, url is predict'

###############################################################################
#----------------- application gateway ------------------
## aiapp application 
# curl -H "Content-Type: application/json" -X POST -d '{"action":"CREATE", "name":"test0017"}' http://localhost:5000/gw/aiapp && echo ""
@gw.route('/gw/aiapp', methods=['POST'])
def aiapp():
    name = request.json.get('name')
    action = request.json.get('action')

    backend = g_backends_map.get(name, None)
    if not backend:
        log.debug("# Available backends: {}".format(g_backends))
        backend = select_provider()
        if backend is None:
            return jsonify({"code": 401, "msg": "No backend available"})
        else:
            g_backends_map[name] = backend
    else:
        log.debug("# {} is handled by {}, reuse it".format(name, backend))
        pass
    url = f"http://{backend.host}:{backend.port}/aiapp"
    headers = {'Content-Type': 'application/json'}
    payload = {'name': name, 'action': action}
    response = requests.post(url, json=payload, headers=headers)
    print("# response: {}".format(response))
    print("# response.status_code: {}".format(response.status_code))
    print("# response.json: {}".format(response.json()))
    return json.dumps(response.json())

###############################################################################
# --------------- provider maintanence ----------------
## register a provider
# curl -H "Content-Type: application/json" -X POST -d '{"service_type":"aiapp","service_version":"1.2.3","host":"127.0.0.1", "port":9999,"url":"aiapp"}' http://localhost:5000/gw/register && echo ""
@gw.route('/gw/register', methods=['POST'])
def reg_provider():
    log.info("# request: {}".format(request))
    log.info("# content-type: {}".format(request.headers['Content-Type']))

    service_type = request.json.get('service_type')
    service_version = request.json.get('service_version')
    host = request.json.get('host')
    port = request.json.get('port') 
    url = request.json.get('url') 
    backend = Backend(service_type,service_version, host,port,url,MAX_TTL)  

    log.info("# Registering: {}:{} {}:{}:{}".format(service_type, service_version, host, port, url))

    # check if the service type is supported
    service_qr = query_service_type(service_type)
    if service_qr is None:
        log.error("# Service type is not supported when registering: {}".format(service_type))
        return jsonify({"code":200, "msg":""})

    # check if the provider has been registered 
    provider_qr = query_provider(service_type, host, port)
    if not provider_qr is None:        
        log.warn("# Provider already registered: {} {}:{}".format(service_type,host,port))
        log.warn("# provider_qr: {} {} {} {}".format(provider_qr.type, provider_qr.version, provider_qr.host, provider_qr.port))
        return jsonify({"code": 200, "msg": "Provider already registered"})
    # backend = Provider(service_type,host,port,url,MAX_TTL) 
    
    
    # if not service_type in g_service_types:
    #     # log.info("# Registered a new service type: {}".format(service_type))
    #     # g_service_types.append(service_type)
    #     log.warn("# Service type not supported: {}".format(service_type))
    #     return jsonify({"code": 200, "msg": "Service type not supported"})
    
    # if backend in g_backends:
    #     log.warn("# Provider already registered.")
    #     return jsonify({"code": 200, "msg": "Provider already registered"})
 

    
    # session = DBSession()
    provider = Provider(type=service_type, version=service_version, host=host, port=port, path=url, ttl=MAX_TTL, active=1, cpuload=0) 
    rtn = add_provider(provider)
    
    # session.add(provider)
    # session.commit()
    # session.close()
    if rtn == 1:
        log.info("# A new provider registered: {} {}:{}".format(service_type,host,port))
        # log.info("# A new backend of type: {}".format(service_type))
        # log.info("# Backend: {}:{}:{} active={} TTL={}".format(backend.host, backend.port, backend.url, backend.active, backend.    ttl))
        # g_backends.append(backend)
        return jsonify({"code": 200, "msg": "OK"})
    else:
        return jsonify({"code": 200, "msg": "Failed"})
    

## update a provider 
# curl -H "Content-Type: application/json" -X POST -d '{"service_type":"aiapp","service_version":"1.2.3","host":"127.0.0.1", "port":9999,"url":"aiapp", "cpuload": "20.0"}' http://localhost:5000/gw/update && echo ""   
@gw.route('/gw/update', methods=['POST'])
def update_provider_stat():
    log.debug("# Got provider update request")
    service_type = request.json.get('service_type')
    service_version = request.json.get('service_version')
    host = request.json.get('host')
    port = request.json.get('port') 
    url = request.json.get('url')     
    cpuload = request.json.get('cpuload')

    provider_up = query_provider(service_type, host, port)

    if provider_up is None:
        log.warn("# Provider not registered : {} {}:{}".format(service_type, host, port))
        return jsonify({"code": 401, "msg": "Provider not registered"}) 
    
    
    # provider_up.ttl = MAX_TTL
    # provider_up.cpuload = cpuload
    # provider_up.active = True
    
    update_provider(service_type, host, port, 1, 3, cpuload)

    # session = DBSession()  
    # session.query(Provider).filter(Provider.type == service_type and Provider.host == host and Provider.port == port).update({Provider.ttl: MAX_TTL, Provider.active: 1, Provider.cpuload: cpuload})
    # session.commit()
    # session.close()

    log.debug("# Provider {}-{}:{} CPU Load: {}%".format(service_type, host, port, cpuload))

    # backend = Backend(service_type,service_version, host,port,url)       
    # if not service_type in g_service_types:
    #     log.info("# Got a new service type: {}".format(service_type))
    #     g_service_types.append(service_type) 
    # try:
    #     index = g_backends.index(backend)
    #     g_backends[index].cpuload = cpuload
    #     g_backends[index].ttl = MAX_TTL
    #     g_backends[index].active = True
    #     log.debug("# Backend {}:{}:{} CPU Load: {}%".format(service_type, host, port, cpuload))
    # except:
    #     g_backends.append(backend)
    #     g_backends[-1].service_type = service_type
    #     g_backends[-1].cpuload = cpuload 
    #     g_backends[-1].ttl = MAX_TTL
    #     g_backends[-1].active = True
    return jsonify({"code": 200, "msg": "OK"}) 
        

def select_provider():
    #global round_robin
    
    #round_robin += 1
    #round_robin = round_robin % len(active_backends)
    min_load = 100
    selected = None

    session = DBSession()
    providers = session.query(Provider).filter(Provider.active == 1).all()
    # providers = query_active_providers()
    print("#type of providers", type(providers))
    print("#length of providers", len(providers))
    for candidate in providers:
        if candidate.active and candidate.cpuload < min_load and candidate.cpuload < CPU_LOAD_THRESHOLD:
            min_load = candidate.cpuload
            selected = candidate    
    log.info("# Select provider: {}".format(selected))
    session.close()
    #active_backends = [n for n in backends if n.active]
    # for candidate in g_backends:
    #     if candidate.active and candidate.cpuload < min_load and candidate.cpuload < CPU_LOAD_THRESHOLD:
    #         min_load = candidate.cpuload
    #         selected = candidate    
    # log.info("# Select backend: {}".format(selected))
    return(selected)
    #log.debug("# active backends: {}".format(len(active_backends)))
    #log.debug("# Select {} in active backends".format(round_robin))
    #return active_backends[round_robin]

###############################################################################    
def sys_init():
    ''' load data from mysql
    1) supported services
    2) registered providers
    3) ongoing tasks
    '''
    # session = DBSession()
    # 1) supported services
    #services = session.query(Service).all()
    log.info("#" * 60)
    log.info("# App gateway starting ...")
    log.info("#" * 60)
    # stmt = select(Service.type).where(Service.valid == 1)
    # result = session.execute(stmt)
    result = query_valid_services()
    #log.info(result)
    log.info("# Supported services:")
    for item in result:
        log.info("#    {}".format(item.type))
        g_service_types.append(item.type)
    log.info("#" * 60)
    # 2) registered providers
    # providers = session.query(Provider).all()
    providers = query_all_providers()
     #log.info(result)
    log.info("# Registered providers:")
    for item in providers:
        log.info("#    {}".format(item.__str__()))
    log.info("#" * 60)
    # 3) ongoing tasks
    # tasks = session.query(Task).all()
    tasks = query_ongoing_tasks()
     #log.info(result)
    log.info("# Ongoing tasks:")
    for item in tasks:
        log.info("#    {}".format(item.__str__()))
    log.info("#" * 60)
    # session.close()

###############################################################################
if __name__=='__main__':
    #schedule.every(5).seconds.do(check_providers)
    sys_init()
    app.debug = True
    app.config.from_object(Config())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(host="0.0.0.0", port=5000, use_reloader=False)