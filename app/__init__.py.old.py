# gateway.py
# curl -H "Content-Type: application/json" -X POST -d '{"action":"CREATE", "name":"test0017"}' http://localhost:5000/aiapp && echo ""
import sys
import configparser
from flask import Flask, Response, make_response, abort, request, jsonify
import requests
import json
from flask_apscheduler import APScheduler
from appgw.fclogger import log
from appgw.backend import Backend
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
from appgw.providerORM import Provider
from appgw.serviceORM import Service
from appgw.taskORM import Task
# import time

# ------------------------------- Init ----------------------------
# init from config file
if len(sys.argv) > 1:
    config_file = sys.argv[1]
else:
    config_file = "/root/src/newappgw/config.ini"
    #config_file = "config.ini"
config = configparser.ConfigParser()
config.read(config_file)

# init DB session
db_host = config["DB"]["HOST"]
db_port = config["DB"]["PORT"]
db_user = config["DB"]["USER"]
db_passwd = config["DB"]["PASSWORD"]
db_name = config["DB"]["DBNAME"]
# init DB link
# engine = create_engine('mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(db_user, db_passwd, db_host, db_port, db_name), echo=False)
engine = create_engine('mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(db_user, db_passwd, db_host, db_port, db_name))
# create DBSession
DBSession = sessionmaker(bind=engine)

# init backend control variables
HEARTBEAT_INTERVAL = int(config['BACKEND_CTRL']['HEARTBEAT_INTERVAL'])
MAX_TTL = int(config['BACKEND_CTRL']['MAX_TTL'])
CPU_LOAD_THRESHOLD = int(config['BACKEND_CTRL']['CPU_LOAD_THRESHOLD'])
# backend variables
g_backends = [] # backends['aiapp'][#]
g_service_types = []
g_backends_map = {}
g_round_robin = 0

# admin allow hosts
HOSTS_ALLOW_ADMIN = config['ADMIN']['HOSTS_ALLOW']

# init Flask
app = Flask(__name__)

###############################################################################
#  define scheduled tasks
class Config(object):
    JOBS = [
        {
            'id': 'job_1',
            'func': '__main__:check_providers',     # 指定运行的函数
            #'args': (999,),              # 传入函数的参数
            'trigger': 'interval',       # 指定 定时任务的类型
            'seconds': 10                # 运行的间隔时间
        },
        {
            'id': 'job_2',
            'func': '__main__:print_stat',     # 指定运行的函数
            #'args': (999,),              # 传入函数的参数
            'trigger': 'interval',       # 指定 定时任务的类型
            'seconds': 60                # 运行的间隔时间
        }
    ]
    SCHEDULER_API_ENABLED = True


###############################################################################
## Flask test page
@app.route('/hello/')
def index():
    return 'this server is running on port:5000, url is predict'

###############################################################################
## admin commands
## admin,  help
@app.route('/admin/help', methods=['GET'])
def adm_gw_help():
    ip = request.remote_addr
    print("# Client IP: {}".format(ip))
    print("# Hosts allowed: {}".format(HOSTS_ALLOW_ADMIN))
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        cmds = ["help", "status", "listp", "listt"]
        return jsonify({"code": 200, "msg": "OK", "Supported commands": cmds})

## admin, list status
@app.route('/admin/status', methods=['GET'])
def adm_gw_status():
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        pass

## admin, list all supported services
@app.route('/admin/lists', methods=['GET'])
def adm_gw_list_services():
    # query_service_type("li")
    # query_service_type("aiapp")    
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        session = DBSession()
        services = session.query(Service).all()
        log.debug("#" * 40)
        log.debug("# There are {} services".format(len(services)))
        for svc in services:      
            #log.debug(type(p))                  
            log.debug(svc)
        log.debug("#" * 40)            
        session.close()
        result = [svc.__str__() for svc in services]
        return jsonify({"code": 200, "msg": "OK", "services": result})        
        #return jsonify({"code": 200, "msg": "OK"})     

## admin, list providers
@app.route('/admin/listp', methods=['GET'])
def adm_gw_list_providers():
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        session = DBSession()
        providers = session.query(Provider).all()     
        log.debug("#" * 40)
        # log.debug(type(providers))
        log.debug("# There are {} providers".format(len(providers)))
        for p in providers:      
            #log.debug(type(p))                  
            log.debug(p)
        log.debug("#" * 40)        
        session.close()
        result = [p.__str__() for p in providers]
        return jsonify({"code": 200, "msg": "OK", "providers": result})        
        #return jsonify({"code": 200, "msg": "OK"})        

## admin, list tasks
@app.route('/admin/listt', methods=['GET'])
def adm_gw_list_tasks():
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        response = make_response('<h2>Not allowed</h2>')
        return response, 404
    else:
        pass

###############################################################################
#----------------- application gateway ------------------
## aiapp application 
@app.route('/aiapp', methods=['POST'])
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
@app.route('/register', methods=['POST'])
def reg_provider():
   # log.info("# request: {}".format(request))
  #  log.info("# content-type: {}".format(request.headers['Content-Type']))

    service_type = request.json.get('service_type')
    service_version = request.json.get('service_version')
    host = request.json.get('host')
    port = request.json.get('port') 
    url = request.json.get('url') 
    backend = Backend(service_type,service_version, host,port,url,MAX_TTL)  

    # check if the service type is supported
    service_qr = query_service_type(service_type)
    if service_qr is None:
        log.error("# Service type is not supported when registering: {}".format(service_type))
        return jsonify({"code":200, "msg":""})

    # check if the provider has been registered 
    provider_qr = query_provider(service_type, host, port)
    if not provider_qr is None:
        log.warn("# Provider already registered: {} {}:{}".format(service_type,host,port))
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
 

    
    session = DBSession()
    provider = Provider(type=service_type, version=service_version, host=host, port=port, path=url, ttl=MAX_TTL, active=1, cpuload=0) 
    session.add(provider)
    session.commit()
    session.close()

    log.info("# A now provider registered: {} {}:{}".format(service_type,host,port))
    # log.info("# A new backend of type: {}".format(service_type))
    # log.info("# Backend: {}:{}:{} active={} TTL={}".format(backend.host, backend.port, backend.url, backend.active, backend.ttl))
    # g_backends.append(backend)
    return jsonify({"code": 200, "msg": "OK"})

## update a provider    
@app.route('/update', methods=['POST'])
def update_provider():
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
    
    session = DBSession()  
    session.query(Provider).filter(Provider.type == service_type and Provider.host == host and Provider.port == port).update({Provider.ttl: MAX_TTL, Provider.active: 1, Provider.cpuload: cpuload})
    session.commit()
    session.close()

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

# query a provider
def query_provider(type, host, port):
    session = DBSession()
    # query = session.query(Provider).filter(
    #     Provider.type == type,
    #     Provider.host == host,
    #     Provider.port == port        
    # )
    # result = session.query(
    #     query.exists()
    # ).scalar()
    try:
        result = session.query(Provider).filter(Provider.type == type and Provider.host == host and Provider.port == port).one_or_none()    
    except:
        log.error("# Found more than 1 service_type :{}".format(service_type))
        result = -1
    else:
        pass
    finally:
        session.close()
    # print("# Provider {} {}:{} exists: {}".format(type,host,port,result))        
    return result

# query a service type
def query_service_type(service_type):
    session = DBSession()      
    try:
        result = session.query(Service).filter(Service.type == service_type and Service.valid == 1).one_or_none()  
    except:
        log.error("# Found more than 1 service_type :{}".format(service_type))
        result = -1
    else:
        pass
    finally:
        session.close()

    # if result is None:
    #     print("# Servcie type {} got {}".format(service_type, result))
    # else:
    #     print("# Servcie type {} got {}".format(service_type, result.type))
    
    return result
    
 # query a task
def query_task(name):
    session = DBSession()
    try:
        result = session.query(Provider).filter(Provider.name == name).one_or_none()    
    except:
        log.error("# Found more than 1 tasks with same name :{}".format(name))
        result = -1
    else:
        print("# Task {} exists: {}".format(name,result))
    finally:
        session.close()
    return result           

# update the status of a task
def update_task(name):
    session = DBSession()
    try:
        result = session.query(Provider).filter(Provider.name == name).one_or_none()    
    except:
        log.error("# Found more than 1 tasks with same name :{}".format(name))
        result = -1
    else:
        print("# Task {} exists: {}".format(name,result))
    finally:
        session.close()
    return result    

def select_provider():
    #global round_robin
    
    #round_robin += 1
    #round_robin = round_robin % len(active_backends)
    min_load = 100
    selected = None

    session = DBSession()
    providers = session.query(Provider).filter(Provider.active == 1).all()
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


def check_providers():
    # for backend in g_backends:
    #     log.info("# Checking {}:{}:{} active={} TTL={}".format(backend.host, backend.port, backend.url,backend.active, backend.ttl))
    #     if backend.active:
    #         try:
    #             requests.get(f"http://{backend.host}:{backend.port}/health")
    #             backend.ttl = MAX_TTL
    #             backend.active = True
    #             log.debug("# Backend {}:{}:{} is active".format(backend.host, backend.port, backend.url))
    #         except:
    #             log.debug("# Backend {}:{}:{} is not responding".format(backend.host, backend.port, backend.url))  
    #             if backend.ttl > 0:    
    #                 backend.ttl -= 1
    #             if backend.ttl <= 0:
    #                 backend.active = False     
    session = DBSession()
    log.debug("# checking providers ...")
    providers = session.query(Provider).filter(Provider.active == 1).all()
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
            session.commit()
        else:
            log.debug("# provider {}:{}:{} is active".format(provider.host, provider.port, provider.path))            
    session.close()



    


###############################################################################    
def sys_init():
    ''' load data from mysql
    1) supported services
    2) registered providers
    3) ongoing tasks
    '''
    session = DBSession()
    # 1) supported services
    #services = session.query(Service).all()
    log.info("#" * 60)
    log.info("# App gateway starting ...")
    log.info("#" * 60)
    stmt = select(Service.type).where(Service.valid == 1)
    result = session.execute(stmt)
    #log.info(result)
    log.info("# Supported services:")
    for item in result:
        log.info("#    {}".format(item.type))
        g_service_types.append(item.type)
    log.info("#" * 60)
    # 2) registered providers
    providers = session.query(Provider).all()
     #log.info(result)
    log.info("# Registered providers:")
    for item in providers:
        log.info("#    {}".format(item.__str__()))
    log.info("#" * 60)
    # 3) ongoing tasks
    tasks = session.query(Task).all()
     #log.info(result)
    log.info("# Ongoing tasks:")
    for item in tasks:
        log.info("#    {}".format(item.__str__()))
    log.info("#" * 60)
    session.close()

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
