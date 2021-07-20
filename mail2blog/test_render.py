#!/usr/bin/env python3
'''Load entries and make a nice view'''
# pylint
# vim: tw=100 foldmethod=indent
#
# This code is distributed under the MIT License
#
# pylint: disable=invalid-name, superfluous-parens
# pylint: disable=logging-fstring-interpolation
# pylint: disable=redefined-outer-name, logging-not-lazy, logging-format-interpolation
# pylint: disable=missing-docstring, trailing-whitespace, trailing-newlines, too-few-public-methods

import logging
import sys
import os
import re
import subprocess
from jinja2 import Template

from mail2blog import logsetup
from mail2blog import tools 
from mail2blog.parse_args import args
from mail2blog.config import CONFIG
from mail2blog.database import Blog_entry, Blog

logger = logging.getLogger(__name__)

md = "# this is a title\n- list1\n- list2\n\ntext text text"

html = tools.render_pandoc_with_theme2(md)

print (html)
