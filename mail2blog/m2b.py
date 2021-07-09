#!/usr/bin/env python3
'''Turn mails to blog entries'''
# This code is distributed under the MIT License
# pylint
# vim: tw=100 foldmethod=indent
#
# This code is distributed under the MIT License
#
# pylint: disable=invalid-name, superfluous-parens
# pylint: disable=mixed-indentation
# pylint: disable=redefined-outer-name, logging-not-lazy, logging-format-interpolation
# pylint: disable=missing-docstring, trailing-whitespace, trailing-newlines, too-few-public-methods

import logging
import sys
from mail2blog import logsetup

from mail2blog.config import CONFIG
from mail2blog.parse_args import args

logger = logging.getLogger(__name__)

def main():
    print ("YES")
    logger.warning("SHURE")
    if args.verbose:
        print("VERBOSE")
    
if __name__ == '__main__':
    sys.exit(main())
