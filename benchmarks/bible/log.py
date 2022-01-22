import logging
import logging.config
import traceback
import math

COLOURS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    'DEBUG': '\033[36m',
    'INFO': '\033[92m',
    'ERROR': '\033[31m',  # red
    'CRITICAL': '\033[1;30;41m',
}
SUFFIX = '\033[0m'


def init_logging(level):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                '()': 'log.ColouredFormatter',
                'format': '%(asctime)s [%(levelnamec)s] %(name)s: %(message)s',
            }
        },
        'handlers': {
            'console': {
                'level': level,
                'formatter': 'default',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            'urllib3.connectionpool': {
                'level': 'ERROR'
            }
        },
        'root': {
            'level': level,
            'handlers': ['console']
        }
    })


class ColouredFormatter(logging.Formatter):

    def format(self, record):
        level = record.levelname
        colour = COLOURS[level]
        pad = (8 - len(level)) / 2
        record.levelnamec = f'{colour}{" "*math.ceil(pad)}{level}{" "*math.floor(pad)}{SUFFIX}'
        return logging.Formatter.format(self, record)


def except2str(e, logger=None):
    if logger:
        tb = traceback.format_exc()
        logger.error(tb)
    return f'{type(e).__name__}: {e}'
