import logging
import logging.handlers
from typing import Any


class ConnRotatingFileHandler(logging.handlers.RotatingFileHandler):
    # override terminator from "\n" to ""
    terminator = ""

    def __init__(self, filename: str, **kwargs) -> None:
        super(self.__class__, self).__init__(filename, **kwargs)
        return


def get_conn_logger(filename: str) -> Any:
    """

    :param filename:
    :return:
    """
    logger = logging.getLogger("CONN-{}".format(filename))
    logger.setLevel(logging.DEBUG)

    rotating_handler = ConnRotatingFileHandler(
        filename,
        mode="a",
        maxBytes=1024 * 1024,
        backupCount=10,
        encoding=None,
        delay=True,
    )
    logger.addHandler(rotating_handler)

    return logger


class EventRotatingFileHandler(logging.handlers.RotatingFileHandler):

    def __init__(self, filename: str, **kwargs) -> None:
        self.__echo = kwargs.get("echo", False)
        del kwargs["echo"]
        super(self.__class__, self).__init__(filename, **kwargs)
        return

    def emit(self, record):
        if self.__echo:
            print(record)
        super(self.__class__, self).emit(record)


def get_event_logger(filename: str, echo: bool = False) -> Any:
    """

    :param filename: log absolute path
    :param echo:
    :return:
    """
    logger = logging.getLogger("EVENT")
    logger.setLevel(logging.DEBUG)

    rotating_handler = EventRotatingFileHandler(
        filename,
        mode="a",
        maxBytes=1024 * 1024,
        backupCount=10,
        encoding=None,
        delay=True,
        echo=echo,
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s|%(levelname)-8s: %(message)s",
        datefmt="%a %d %b %Y %H:%M:%S",
    )
    rotating_handler.setFormatter(formatter)
    logger.addHandler(rotating_handler)
    return logger
