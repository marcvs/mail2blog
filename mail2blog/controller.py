#!/usr/bin/env python3
'''Turn mails to blog entries'''
# This code is distributed under the MIT License
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
from sys import stdin
import os
import mimetypes
import email
from email.iterators import _structure

from mail2blog import logsetup
from mail2blog import tools 
from mail2blog.config import CONFIG
from mail2blog.parse_args import args
from mail2blog.database import Blog_entry

logger = logging.getLogger(__name__)


def main():
    msg = email.message_from_string(stdin.read())

    #  Now the header items can be accessed as a dictionary:
    print('To: {}'.format(msg['to']))
    print('From: {}'.format(msg['from']))
    print('Subject: {}'.format(msg['subject']))

    # You can also access the parts of the addresses:
    print('Recipient username: {}'.format(msg['to']))
    print('Sender name: {}'.format(msg['from']))


def parse_mail():
    '''Decompose email and store in database and raw_folder'''
    raw = stdin.read()
    msg = email.message_from_string(raw)
    FIELDS = ['from', 'to', 'subject', 'date', 'Message-ID', 'Return-Path', 'Content-Type']
    dec_msg = {}
    for field in FIELDS:
        dec_msg[field] = tools.email_decode(msg[field])

    # print(F'message keys: {msg.keys()}\n')
    print(F'To:          {dec_msg["to"]}')
    print(F'From:        {dec_msg["from"]}')
    print(F'Subject:     {dec_msg["subject"]}')
    print(F'Date:        {dec_msg["date"]}')
    print(F'Message-ID   {dec_msg["Message-ID"]}')
    print(F'Return-Path: {dec_msg["Return-Path"]}')

    blog_entry = Blog_entry(msg['message-id'].replace('<', '').replace('>',''), msg['from'], msg['subject'])
    blog_entry.store_in_db()
    # print(F"\nbody:{msg.get_body('plain', 'html', 'related')}")
    # print(F'Content-Type: {dec_msg["Content-Type"]}')

    # print(_structure(msg))

    directory = CONFIG.get('locations', 'raw_output', fallback='/tmp/mail2blog') 
    directory += "/" + msg["Message-ID"].replace('<','').replace('>','')

    logger.info(F"Storing incoming messge >>{dec_msg['subject']}<< of {dec_msg['from']} to {directory}")
    tools.makepath(directory)

    with open(os.path.join(directory, 'raw.mail'), 'w') as fp:
        fp.write(raw)

if __name__ == '__main__':
    # sys.exit(main())
    sys.exit(parse_mail())
