# coding=utf-8
import logging

__author__ = "Luke"
__version__ = "0.0.1"


class DefaultLogging:
    LoggingLevel = logging.INFO

    # create console handler and set level to debug
    CmdHandler = logging.StreamHandler()
    CmdHandler.setLevel(LoggingLevel)

    # create formatter
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    CmdHandler.setFormatter(formatter)


def get_logger(name, handler=DefaultLogging.CmdHandler):
    logger = logging.getLogger(name)
    logger.setLevel(DefaultLogging.LoggingLevel)
    logger.addHandler(handler)
    return logger
