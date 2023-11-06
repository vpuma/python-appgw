# coding: utf-8
from sqlalchemy import Column, Float, String, TIMESTAMP, text, DateTime
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.ext.declarative import declarative_base
import psutil

Base = declarative_base()
metadata = Base.metadata


class Provider(Base):
    __tablename__ = 'provider'

    id = Column(INTEGER(11), primary_key=True, comment='设置主键自增')
    type = Column(String(100), nullable=False, comment='service type, i.e. aiapp')
    version = Column(String(100), nullable=False, comment='service version, i.e. 1.0.2')
    host = Column(String(100), nullable=False, comment='host, i.e. 192.168.0.12')
    port = Column(INTEGER(11), nullable=False, comment='port, i.e. 8010')
    path = Column(String(100), nullable=False, comment='path, i.e. /aipp')
    ttl = Column(INTEGER(11), nullable=False, comment='TTL, a countdown value, >0 active <=0 inactive')
    active = Column(TINYINT(1), nullable=False, comment='if actige, 1-active  0-inactive')
    cpuload = Column(Float, nullable=False, comment='cpu load, i.e. 25.03')
    update_timestamp = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='timestamp of the last update')

    def __init__(self, type, version, host, port, path, ttl, active, cpuload, id=None, update_timestamp=None):   
        self.id = id  
        self.type = type
        self.version = version
        self.host = host
        self.port = port
        self.path = path
        self.ttl = ttl
        self.active = active
        self.cpuload = cpuload
        self.update_timestamp = update_timestamp

    def get_cpuload(self):
        self.cpuload = psutil.cpu_percent()

    def __eq__(self, other):
        if self.type==other.type and self.host==other.host and self.port==other.port:
            return True
        else:
            return False

    def __str__(self):
        return "{}:{}:{}".format(self.type, self.host, self.port)


class Service(Base):
    __tablename__ = 'service'

    id = Column(INTEGER(11), primary_key=True, comment='设置主键自增')
    type = Column(String(100), nullable=False, comment='service type, i.e. aiapp')
    stateless = Column(TINYINT(1), nullable=False, comment='1-stateless  0-not stateless')
    valid = Column(TINYINT(1), nullable=False, comment='1-valid  0-invalid')
    #version = Column(String(100), nullable=False, comment='service version, i.e. 1.0.2')

    def __init__(self, type, stateless, valid, id=None):
        self.type = type
        self.stateless = stateless
        self.valid = valid
        self.id = id

    def __eq__(self, other):
        if self.type==other.type:
            return True
        else:
            return False

    def __str__(self):
        return "{} stateless:{} valid:{}".format(self.type, self.stateless, self.valid)

class Task(Base):
    __tablename__ = 'task'

    id = Column(INTEGER(11), primary_key=True, comment='设置主键自增')
    name = Column(String(500), nullable=False, comment='task name, i.e. nlt01.vtc365.com_4025_99395')
    provider_id = Column(INTEGER(11), nullable=False, comment='provider id in table provider')
    create_time = Column(DateTime, nullable=False, comment='time of creating, i.e. 20230618 15:00:20')
    status = Column(String(50), nullable=False, comment='task status, i.e. CREATING, IP, STOPPED')
    video_url = Column(String(500), nullable=False, comment='video url, i.e. http://test.vtc365.com/s22/1234/live.m3u8')
    update_timestamp = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment='timestamp of the last update')

    def __init__(self, name, provider_id, create_time, status, video_url, id=None, update_timestamp=None):   
        self.id = id  
        self.name = name
        self.provider_id = provider_id
        self.create_time = create_time
        self.status = status
        self.video_url = video_url
        self.update_timestamp = update_timestamp

    def __str__(self):
        return "{} on provider {} with video {} {}".format(self.name, self.provider_id, self.video_url, self.status)
