import logging

def setup_logger(level):
    logging.basicConfig(format='[%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S', level=level)
    logger = logging.getLogger('gains')
    return logger