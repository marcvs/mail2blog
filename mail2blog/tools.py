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

