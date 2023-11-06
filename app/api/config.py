import os
import sys
import configparser
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

basedir = os.path.abspath(os.path.dirname(__file__))

def init_config():
    # init from config file
    if len(sys.argv) > 2 and sys.argv[0] == "gunicorn":
        config_file = sys.argv[2]
    elif len(sys.argv) > 1 and sys.argv[0] == "flask":
        config_file = sys.argv[1]
    else:
        config_file = "app/config.ini"
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def init_db_session(config):

    # init DB session
    db_host = config["DB"]["HOST"]
    db_port = config["DB"]["PORT"]
    db_user = config["DB"]["USER"]
    db_passwd = config["DB"]["PASSWORD"]
    db_name = config["DB"]["DBNAME"]
    engine = create_engine('mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(db_user, db_passwd, db_host, db_port, db_name))
    # create DBSession
    DBSession = sessionmaker(bind=engine,expire_on_commit=False)
    return DBSession

