# pylint 
# vim: tw=100 foldmethod=indent
# pylint: disable=invalid-name, superfluous-parens
# pylint: disable=mixed-indentation
# pylint: disable=redefined-outer-name, logging-not-lazy, logging-format-interpolation
# pylint: disable=missing-docstring, trailing-whitespace, trailing-newlines, too-few-public-methods

import logging
from logging.handlers import RotatingFileHandler

from .parse_args import args
from .config import CONFIG

# logger = logging.getLogger(__name__)
logger = logging.getLogger('')  # => This is the key to allow logging from other modules

class PathTruncatingFormatter(logging.Formatter):
    '''formatter for logging'''
    def format(self, record):
        pathname = record.pathname
        if len(pathname) > 23:
            pathname = '...{}'.format( pathname[-19:])
        record.pathname = pathname
        return super(PathTruncatingFormatter, self).format(record)

def setup_logging():
    '''setup logging'''

    # Define Formatter
    formatter = logging.Formatter("[%(asctime)s]%(levelname)8s - %(message)s")

    if args.debug:
        args.loglevel = "DEBUG"
        formatter  = PathTruncatingFormatter(
                "[%(asctime)s] {%(pathname)23s:%(lineno)-3d}%(levelname)8s - %(message)s")

    # Logfile setup
    # First try config
    logfile = CONFIG.get('main', 'logfile',  fallback = None)
    # Then overwrite by commandline
    if args.logfile not in [None, '']:
        logfile = args.logfile
    # and then set it
    if logfile is not None:
        handler = RotatingFileHandler(logfile, maxBytes=10**6, backupCount=2)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Loglevel setup (similar as file)
    loglevel = CONFIG.get('main', 'loglevel',  fallback = None)
    if args.loglevel is not None: # If set via Environment, its set here already
        loglevel = args.loglevel.upper()
    if loglevel is None: # set the default:
        loglevel = "WARNING"

    logger.setLevel(loglevel)
    # logger.info('------------------------------------- new start -----------------')

    # turn off werkzeug logging:
    werkzeug_log = logging.getLogger('werkzeug')
    werkzeug_log.setLevel(logging.CRITICAL)
    werkzeug_log.addHandler(handler)
    return logger

logger = setup_logging()
