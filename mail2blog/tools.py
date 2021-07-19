#!/usr/bin/env python3
# pylint
# vim: tw=100 foldmethod=indent
#
# This code is distributed under the MIT License
#
# pylint: disable=invalid-name, superfluous-parens
# pylint: disable=logging-fstring-interpolation
# pylint: disable=redefined-outer-name, logging-not-lazy, logging-format-interpolation
# pylint: disable=missing-docstring, trailing-whitespace, trailing-newlines, too-few-public-methods

import os
import email
from datetime import datetime
import pypandoc
from html.entities import codepoint2name

from mail2blog.config import CONFIG

def makepath(directory, depth=3):
    basepath = '/'.join(directory.split('/')[0:-depth])
    snippets = directory.split('/')[-depth:]

    paths = []
    for i in range(0, len(snippets)):
        paths.append(basepath +'/'+'/'.join(snippets[0:i+1]))

    for path in paths: 
        # logger.debug(F"making: {path}")
        try:
            os.mkdir(path)
        except FileExistsError as e:
            # logger.warning(F"Cannot create directory: {e}")
            pass

def email_decode(value):
    '''Decode email encoding'''
    return email.header.make_header(email.header.decode_header(value))

def dateparser(text):
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%m/%d/%y %H:%M', '%m/%d/%Y %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(F'no valid date format found: >>{text}<<')

# >>Tue, 13 Jul 2021 10:52:08 +0200<<
def render_pandoc_with_theme(inpt, title="Title"):
    style_file_name = CONFIG.get('themes', 'style_file', fallback=None) 
    with open(style_file_name, 'r') as st:
        style = st.read()

    pandoc_args = ['-s']
    header = F'title: {title}\n---\n'

    html_data = pypandoc.convert_text(style + inpt, 'html', format='md', extra_args=pandoc_args)
    return html_data

def htmlescape(text):
    '''escape html characters'''
    d = dict((chr(code), u'&%s;' % name) for code,name in codepoint2name.items() if code!=38) # exclude "&"    
    if u"&" in text:
        text = text.replace(u"&", u"&amp;")
    for key, value in d.items():
        if key in text:
            text = text.replace(key, value)
    return text
