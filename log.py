import logging


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s %(threadName)s/%(levelname)s] %(message)s",
                                  "%H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger