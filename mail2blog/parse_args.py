# pylint
# vim: tw=100 foldmethod=indent
# pylint: disable=bad-continuation, invalid-name, superfluous-parens
# pylint: disable=bad-whitespace, mixed-indentation
# pylint: disable=redefined-outer-name, logging-not-lazy, logging-format-interpolation
# pylint: disable=missing-docstring, trailing-whitespace, trailing-newlines, too-few-public-methods

import os
import sys
import logging
import argparse

logger = logging.getLogger(__name__)

def parseOptions():
    '''Parse the commandline options'''

    folder_of_executable = os.path.split(sys.argv[0])[0]
    # basename = os.path.basename(sys.argv[0]).rstrip('.py')
    # print (F"basename: {basename}")
    basename="mail2blog"

    # config_dir  = os.environ['HOME']+F'/.config/{basename}'
    config_file = os.environ['HOME']+F'/.config/{basename}.conf'
    db          = os.environ['HOME']+F'/.cache/{basename}.db'
    # log_file    = os.environ['HOME']+F'/.cache/{basename}.log'
    log_file    = folder_of_executable+F'/{basename}.log'
    log_file    = ''

    # if not os.path.exists(config_dir):
    #     os.mkdir(config_dir)

    parser = argparse.ArgumentParser(description='''mail2blog''')
    parser.add_argument('--basename'        ,default=basename)
    parser.add_argument('--logfile'         ,default=log_file, help='logfile' )
    parser.add_argument('--config',   '-c'  ,default=config_file)
    parser.add_argument('--port'            ,default=3888)
    # parser.add_argument('--loglevel'        ,default=os.environ.get("LOG", "WARNING").upper()
    #                                         ,help='Debugging Level')
    parser.add_argument('--loglevel'        ,default=os.environ.get("LOG", None)
                                            ,help='Debugging Level')

    parser.add_argument('--message',  '-m'  ,default=None, type=int)
    parser.add_argument('--list-messages',  '-lm'  ,default=False, action="store_true")
    parser.add_argument('--debug',    '-d'  ,default=False, action="store_true")
    parser.add_argument('--verbose',  '-v'  ,default=False, action="store_true")
    parser.add_argument('--nopix',           default=False, action="store_true")
    parser.add_argument('--force',    '-f',  default=False, action="store_true")
    # parser.add_argument(dest='target_file'   ,default=None,
    #         nargs='*', help='Just an example')

    args = parser.parse_args()

    return args

# reparse args on import
args = parseOptions()
