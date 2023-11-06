import logging
from logging import Logger
from logging.handlers import TimedRotatingFileHandler


def init_logger(logger_name):
    if logger_name not in Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        # handler all
        handler = TimedRotatingFileHandler('logs/all.log', when='midnight', backupCount=7)
        datefmt = "%Y-%m-%d %H:%M:%S"
        format_str = "[%(asctime)s]: [%(process)d] %(levelname)s %(filename)s %(lineno)s %(message)s"
        formatter = logging.Formatter(format_str, datefmt)
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        # handler error
        handler = TimedRotatingFileHandler('logs/error.log', when='midnight', backupCount=7)
        datefmt = "%Y-%m-%d %H:%M:%S"
        format_str = "[%(asctime)s]: [%(process)d] %(levelname)s %(filename)s %(lineno)s %(message)s"
        formatter = logging.Formatter(format_str, datefmt)
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
    logger = logging.getLogger(logger_name)
    return logger


log = init_logger('GW')


# Testing
if __name__ == '__main__':
    log = init_logger('FC')
    log.error("test-error")
    log.info("test-info")
    log.warning("test-warn")
