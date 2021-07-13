#!/usr/bin/env python3
'''Turn mails to blog entries'''
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
import email
from email.iterators import _structure
from imaplib import IMAP4_SSL

from mail2blog import logsetup
from mail2blog import tools
from mail2blog.config import CONFIG
# from mail2blog.parse_args import args

logger = logging.getLogger(__name__)

def test():
    host       = CONFIG.get('imap', 'host')
    imap_debug = CONFIG.getint('imap', 'debug', fallback = 0)
    user       = CONFIG.get('imap', 'user')
    passwd     = CONFIG.get('imap', 'pass')

    M          = IMAP4_SSL(host)
    M.debug    = imap_debug
    res        = M.login(user, passwd)
    if res[0] != 'OK':
        logger.error(F"Problem logging in to IMAP: {res}")
    M.enable("UTF8=ACCEPT")
    M.select(readonly=True)

    res, data = M.search(None, 'ALL')
    for num in data[0].split():
        # res, data = M.fetch(num, '(RFC822)')
        res, data = M.fetch(num, '(BODY[HEADER])')
        # print(F"---\n{data[0][1]}\n---")
        msg = email.message_from_string(data[0][1].decode('iso-8859-1'))
        FIELDS = ['from', 'to', 'subject', 'date', 'Message-ID', 'Return-Path', 'Content-Type']
        dec_msg = {}
        for field in FIELDS:
            dec_msg[field] = tools.email_decode(msg[field])
        dec_msg['message-id']=msg['message-id'].replace('<','').replace('>','')
        print(F"{dec_msg['message-id']:36} | {dec_msg['from']} | {msg['to']:21} |  {dec_msg['subject']} | {msg['date']}")
        # print(F"structure:\n  {_structure(msg)}")

    print ('---')
    ### get full mail by message id:

    # typ, msgnums = M.search(None, '(FROM "LDJ")')
    # typ, msgnums = M.search(None, 'FROM', '"LDJ"')
    # res, data = M.search(None, '(UID SEARCH HEADER Message-ID <YO1RCObSzbq6V4wq@nemo.hardt-it.de>)')
    # keys: ['HEADER', 'MESSAGE-ID', message_id]
    res, data = M.search(None, '(HEADER "Message-ID" "<YO1RCObSzbq6V4wq@nemo.hardt-it.de>")')
    print (res)
    res, data = M.fetch(num, '(RFC822)')
    print (res)
    msg = email.message_from_string(data[0][1].decode('iso-8859-1'))

    print(F"{msg['from']:40} | {msg['to']:40} |  {msg['subject']:30}")

    M.close()
    M.logout()

class ImapConnector():
    def __init__(self):
        self.connected = False

    def connect(self):
        host           = CONFIG.get('imap', 'host')
        imap_debug     = CONFIG.getint('imap', 'debug', fallback = 0)
        user           = CONFIG.get('imap', 'user')
        passwd         = CONFIG.get('imap', 'pass')
        self.M         = IMAP4_SSL(host)
        self.M.debug   = imap_debug
        res        = self.M.login(user, passwd)
        if res[0] != 'OK':
            logger.error(F"Problem logging in to IMAP: {res}")
        self.M.enable("UTF8=ACCEPT")
        self.M.select(readonly=True)
        self.connected=True

    def __del__(self):
        '''disconnect from imap'''
        try:
            if self.connected is True:
                self.disconnect()
        except Exception as e:
            pass
            # logger.warning("Imap could not disconnect. Was probably already disconnected")
            # logger.warning(e)

    def disconnect(self):
        self.M.close()
        self.M.logout()
        self.connected = False


    def get_message_list(self):
        if not self.connected:
            self.connect()
        res, data = self.M.search(None, 'ALL')
        msg_list = []
        for num in data[0].split():
            # res, data = M.fetch(num, '(RFC822)')
            res, data = self.M.fetch(num, '(BODY[HEADER])')
            # print(F"Message #{int(num)} ")
            # print(F"---\n{data[0][1]}\n---")
            msg_list.append (email.message_from_string(data[0][1].decode('iso-8859-1')))
        return msg_list

    def get_message(self, message_id):
        if not self.connected:
            self.connect()
        # res, data = self.M.search(None,  '(HEADER "Message-ID" "<YO1ZCXx5apR53NRG@nemo.hardt-it.de>")')
        res, data = self.M.search(None, F'(HEADER "Message-ID" "<{message_id}>")')
        if res != 'OK':
            logger.error(F"Problem finding message in IMAP: {res}")
        res, data = self.M.fetch(data[0], '(RFC822)')
        if res != 'OK':
            logger.error(F"Problem fetching from IMAP: {res}")
        msg = email.message_from_string(data[0][1].decode('iso-8859-1'))
        return msg




if __name__ == '__main__':
    # sys.exit(main())
    sys.exit(test())


