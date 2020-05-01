import logging
import logging.handlers


__author__ = "Robin Wu"



class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
        Create this class is to override 'terminator' to ''
    """
    terminator = ''

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=True):
        super().__init__(
            filename=filename,
            mode=mode,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay
            )


def get_logger(name):
    """
    :param name: log absolute path
    :return:
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    rotating_handler = RotatingFileHandler(filename=name,
                                           mode='a',
                                           maxBytes=1024 * 1024,
                                           backupCount=10
                                           )
    logger.addHandler(rotating_handler)

    return logger
