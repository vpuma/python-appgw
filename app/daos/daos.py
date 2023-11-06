from app.services.fclogger import log
from app.models.models import Provider
from app.models.models import Service
from app.models.models import Task
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from app.api.config import init_config, init_db_session

config = init_config()
DBSession = init_db_session(config)
HEARTBEAT_INTERVAL = int(config['BACKEND_CTRL']['HEARTBEAT_INTERVAL'])
MAX_TTL = int(config['BACKEND_CTRL']['MAX_TTL'])
CPU_LOAD_THRESHOLD = int(config['BACKEND_CTRL']['CPU_LOAD_THRESHOLD'])

# query a provider
def query_provider(type, host, port):
    session = DBSession()
    try:
        result = session.query(Provider).filter(Provider.type==type, Provider.host==host, Provider.port==port).one_or_none()
    except:
        log.error("# Found more than 1 provider :{}:{}:{}".format(type, host, port))
        result = -1
    else:
        pass
    finally:
        log.debug("# query_provider result: {}".format(result))
        session.close()
    # print("# Provider {} {}:{} exists: {}".format(type,host,port,result))        
    return result

# query all providers
def query_all_providers():
    session = DBSession()
    try:
        providers = session.query(Provider).all()
    except:
        log.error("# Failed to query providers")
    else:
        pass
    finally:
        session.close()
    # print("# Provider {} {}:{} exists: {}".format(type,host,port,result))        
    return providers

# query active providers
def query_active_providers():
    session = DBSession()
    try:
        providers = session.query(Provider).filter(Provider.active == 1).all()
    except:
        log.error("# Failed to query providers")
    else:
        pass
    finally:
        session.close()
    # print("# Provider {} {}:{} exists: {}".format(type,host,port,result))        
    return providers

# add a provider
def add_provider(provider2add: Provider):
    log.info("## Servcie: {}".format(provider2add))
    session = DBSession()
    try:
        session.add(provider2add)
        session.commit()      
    except:
        log.error("# Failed to insert into table provider")
        result = -1
    else:
        log.info("# Successfully inserted into table provider")
        result = 1
    finally:
        session.close()
    return result

# update a provider
def update_provider(service_type, host, port, active, ttl=3, cpuload=None):
    log.debug("# updating provider: {}:{}:{}:{}".format(service_type, host, port, cpuload))

    session = DBSession()  
    if cpuload is None:
        session.query(Provider).filter(Provider.type == service_type, Provider.host == host, Provider.port == port).update({Provider.ttl: ttl, Provider.active: active})
    else:
        session.query(Provider).filter(Provider.type == service_type, Provider.host == host, Provider.port == port).update({Provider.ttl: ttl, Provider.active: active, Provider.cpuload: cpuload})
    session.commit()
    session.close()
    

# query a service type
def query_service_type(service_type):
    session = DBSession()   
    try:
        log.debug("# querying service type: {}".format(service_type))
        result = session.query(Service).filter(Service.type == service_type, Service.valid == 1).one_or_none()   
    except Exception as e:
        log.error("# Exception :{}".format(e))
        result = -1
    finally:
        log.debug("# query_service_type result: {}".format(result))
        session.close()

    # if result is None:
    #     print("# Servcie type {} got {}".format(service_type, result))
    # else:
    #     print("# Servcie type {} got {}".format(service_type, result.type))
    
    return result

# query all servcie types
def query_all_services():
    session = DBSession()
    try:
        services = session.query(Service).all() 
    except:
        log.error("# Failed to query tasks")
    else:
        pass
    finally:
        session.close()
    return services

# query valid servcie types
def query_valid_services():
    session = DBSession()
    services = []
    try:
        services = session.query(Service).filter(Service.valid == 1).all() 
    except:
        log.error("# Failed to query tasks")
    else:
        pass
    finally:
        session.close()
    return services

# add a service type
def add_service_type(service2add: Service):
    log.info("## Servcie: {}".format(service2add))
    session = DBSession()
    try:
        session.add(service2add)
        session.commit()      
    except:
        log.error("# Failed to insert into table service")
        result = -1
    else:
        log.info("# Successfully inserted into table service")
        result = 1
    finally:
        session.close()
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

# query all tasks
def query_all_tasks():
    session = DBSession()
    try:
        tasks = session.query(Task).all() 
    except:
        log.error("# Failed to query tasks")
    else:
        pass
    finally:
        session.close()
    return tasks

# query ongoing tasks
def query_ongoing_tasks():
    session = DBSession()
    try:
        tasks = session.query(Task).filter(Task.status != 'STOPPED').all() 
    except:
        log.error("# Failed to query tasks")
    else:
        pass
    finally:
        session.close()
    return tasks

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