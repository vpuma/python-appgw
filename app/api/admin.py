# gateway.py
# curl -H "Content-Type: application/json" -X POST -d '{"action":"CREATE", "name":"test0017"}' http://localhost:5000/aiapp && echo ""
import sys
import configparser
from flask import Flask, Response, make_response, abort, request, jsonify
import requests
import json
from flask_apscheduler import APScheduler
from app.services.fclogger import log
from app.services.backend import Backend
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
from app.models.models import Provider
from app.models.models import Service
from app.models.models import Task
from app.daos.daos import query_provider, query_service_type, add_service_type, query_all_providers, query_all_tasks, query_all_services
from .config import init_config
# import time

from flask import Blueprint
admin = Blueprint('myadmin', __name__)

# ------------------------------- Init ----------------------------
config = init_config()
# admin allow hosts
HOSTS_ALLOW_ADMIN = config['ADMIN']['HOSTS_ALLOW']


###############################################################################
## Flask test page
@admin.route('/admin/hello/')
def index():
    return 'this server is running on port:5000, url is predict'

###############################################################################
## admin commands
## admin,  help
@admin.route('/admin/help', methods=['GET'])
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
@admin.route('/admin/status', methods=['GET'])
def adm_gw_status():
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        pass

## admin, list all supported services
@admin.route('/admin/lists', methods=['GET'])
def adm_gw_list_services():
    # query_service_type("li")
    # query_service_type("aiapp")    
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        services = query_all_services()
        log.debug("#" * 40)
        log.debug("# There are {} services".format(len(services)))
        for svc in services:      
            #log.debug(type(p))                  
            log.debug(svc)
        log.debug("#" * 40)            
        # session.close()
        result = [svc.__str__() for svc in services]
        return jsonify({"code": 200, "msg": "OK", "services": result})        
        #return jsonify({"code": 200, "msg": "OK"})

## admin, add a new service
# curl -H "Content-Type: application/json" -X POST -d '{"type":"testservice", "stateless":0, "valid":1}' http://localhost:5000/admin/adds && echo ""
@admin.route('/admin/adds', methods=['POST'])
def adm_gw_add_service():  
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        
        json_data = request.json
        log.info(f"json_data:{json_data}")
        if "type" not in json_data:
            log.error("# type is required")
            return jsonify({"code": 200, "msg": "Failed", "Reason": "type is required"})
        if "stateless" not in json_data:
            log.error("# stateless is required")
            return jsonify({"code": 200, "msg": "Failed", "Reason": "stateless is required"})
        if "valid" not in json_data:
            log.error("# valid is required")
            return jsonify({"code": 200, "msg": "Failed", "Reason": "valid is required"})
        

        service_qr = query_service_type(json_data["type"])
        if not service_qr is None:
            log.warn("# Service type already exists: {}".format(json_data["type"]))
            return jsonify({"code":200, "msg":"Service type already exists"})
        service = Service(json_data["type"],json_data["stateless"],json_data['valid'])
        
        rtn = add_service_type(service)

        log.info("#" * 40)
        if rtn == 1:
            log.debug("# A new servcie has been added: {}".format(service.type) )
            log.info("#" * 40)
            return jsonify({"code": 200, "msg": "OK", "New servcie added": service.type})  
        else:
            log.error("# Failed to add service type: {}".format(service.type))
            log.info("#" * 40)
            return jsonify({"code": 200, "msg": "OK", "Failed to add": service.type})  
        # log.info("# Servcie: {}".format(service))
                 

## admin, list providers
@admin.route('/admin/listp', methods=['GET'])
def adm_gw_list_providers():
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        return 404
    else:
        providers = query_all_providers()
        log.debug("#" * 40)
        # log.debug(type(providers))
        log.debug("# There are {} providers".format(len(providers)))
        for p in providers:      
            #log.debug(type(p))                  
            log.debug(p)
        log.debug("#" * 40)        
        #session.close()
        result = [p.__str__() for p in providers]
        return jsonify({"code": 200, "msg": "OK", "providers": result})        
        #return jsonify({"code": 200, "msg": "OK"})        

## admin, list tasks
@admin.route('/admin/listt', methods=['GET'])
def adm_gw_list_tasks():
    ip = request.remote_addr
    if not ip in HOSTS_ALLOW_ADMIN:
        response = make_response('<h2>Not allowed</h2>')
        return response, 404
    else:
        tasks = query_all_tasks()    
        log.debug("#" * 40)
        # log.debug(type(tasks))
        log.debug("# There are {} tasks".format(len(tasks)))
        for t in tasks:      
            #log.debug(type(p))                  
            log.debug(t)
        log.debug("#" * 40)        
        result = [t.__str__() for t in tasks]
        return jsonify({"code": 200, "msg": "OK", "tasks": result})        
        #return jsonify({"code": 200, "msg": "OK"})   
