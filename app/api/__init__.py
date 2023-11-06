import sys
import configparser
from .admin import admin
from .gateway import gw


DEFAULT_BLUEPRINT = [
    (admin, '/'),
    (gw,'/')
]


def config_blueprint(app):
    for blueprint, prefix in DEFAULT_BLUEPRINT:
        app.register_blueprint(blueprint, url_prefix=prefix)
