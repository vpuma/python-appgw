import psutil

class Backend:

    def __init__(self, service_type, service_version, host, port, url, ttl=0, active=True, cpuload=None):
        self.service_type = service_type # "aiapp"
        self.service_version = service_version
        self.host = host
        self.port = port
        self.url = url
        self.ttl = ttl
        self.active = active
        self.cpulod = cpuload

    def get_cpuload(self):
        self.cpuload = psutil.cpu_percent()

    def __eq__(self, other):
        if self.service_type==other.service_type and self.host==other.host and self.port==other.port and self.url==other.url:
            return True
        else:
            return False

    def __str__(self):
        return "{}:{}:{}".format(self.host, self.port, self.url)