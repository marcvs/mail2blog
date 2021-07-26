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
import sqlite3
import time
import email
import re

from email.iterators import _structure
from imaplib import IMAP4_SSL
from datetime import datetime
from jinja2 import Template

from mail2blog import logsetup
from mail2blog.imapconnector import ImapConnector
from mail2blog import tools
from mail2blog.config import CONFIG
# from mail2blog.parse_args import args

logger = logging.getLogger(__name__)
imap = ImapConnector()

def dict_factory(cursor, row):
    '''helper for json export from sqlite'''
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class Blog_entry:
    '''Store single blog entries in th database'''
    db_was_initialised = False

    def __init__(self, message_id=None, email_from=None, subject=None, epoch=None, source="db"):
        # logger.debug("INIT bog_entry")
        self.message_id = message_id
        self.email_from = email_from
        # self.subject    = subject
        self.subject    = tools.email_decode(subject)
        self.source     = source

        self.epoch      = epoch
        if epoch is None:
            self.epoch  = int(time.time())

        self.date = datetime.fromtimestamp(epoch)
        self.author = str(email_from).split('<')[0]
        self.author_email = str(email_from).split('<')[1].replace('>','')
        
    # def initSqlTables(self, database):
    def initSqlTables(self):
        '''helper to initialise sql db'''
        # Setup SQL tables
        conn = sqlite3.connect(CONFIG.get('locations', 'database', fallback = None))
        cur = conn.cursor()
        try:
            cur.execute('''create table if not exists mail2blog '''
                '''(date REAL, message_id TEXT NOT NULL UNIQUE, email_from TEXT, subject TEXT)''')
            cur.execute('''create index if not exists name_index ON mail2blog(message_id)''')
            cur.execute('''create index if not exists date_index ON mail2blog(date)''')
            conn.commit()
            conn.close()

        except sqlite3.OperationalError as e:
            logger.error("SQL Create error: " + str(e))
            raise
        self.db_was_initialised = True
        
    def get_message_id(self):
        return self.message_id

    def get_message(self):
        logger.info(F"loading message {self.subject}...")
        if self.source == "db":
            msg = self.get_message_from_db()
        elif self.source == "imap":
            msg = self.get_message_from_imap()
        return msg

    def get_message_from_db(self):
        directory = CONFIG.get('locations', 'raw_output', fallback='/tmp/mail2blog') 
        directory += "/" + self.message_id
        msg_file = open(directory + "/raw.mail", 'r')
        msg = email.message_from_file(msg_file)
        # msg = self._decode_message(msg)
        return msg

    def get_message_from_imap(self):
        msg = imap.get_message(self.message_id)
        # msg = self._decode_message(msg)
        return msg

    def _decode_message(self, msg):
        FIELDS = ['from', 'to', 'subject', 'date', 'Return-Path', 'Content-Type']
        dec_msg = {}
        for field in FIELDS:
            dec_msg[field] = tools.email_decode(msg[field])
        dec_msg['message-id']=msg['message-id'].replace('<','').replace('>','')
        return dec_msg

    def get_subject(self, replace_spaces=False):
        if not replace_spaces:
            return self.subject
        s = re.sub(r"[^\w\s]", '', str(self.subject))
        s = re.sub(r"[\s+/-]", '_', s)
        return s

    def store_in_db(self):
        '''store entry in db'''
        if not self.db_was_initialised:
            self.initSqlTables()
        conn = sqlite3.connect(CONFIG.get('locations', 'database', fallback = None))
        cur  = conn.cursor()
        try:
            cur.execute('''insert into mail2blog values(%f, '%s', '%s', '%s')''' %
                    (self.epoch, self.message_id, self.email_from, self.subject))
            conn.commit()
            conn.close()
            logging.info('Stored entry in db: %s' % str(self))

        except sqlite3.OperationalError as e:
            logger.error("SQL Create error: " + str(e))
            logger.error("'''insert into mail2blog values(%f, '%s', %s, '%s')'''" %
                    (self.epoch, self.message_id, self.email_from, self.subject))
            raise
        except sqlite3.IntegrityError:
            logger.warning(F"we seem to have a dupe: {self.message_id}")
    @classmethod
    def from_json(cls, json):
        '''create new entry from json'''
        return (cls(json['message_id'], json['email_from'], json['subject'], json['date']))

    def __str__(self):
        template_file = CONFIG.get('templates', 'index')
        with open(template_file, 'r') as fh:
            template_data = fh.read()
        template = Template(template_data)
        subject_no_spaces = self.get_subject(replace_spaces=True)
        retval = template.render(date = self.date, 
                                subject = self.subject,
                                author = self.author,
                                author_first = self.author.split(' ')[0],
                                author_last  = self.author.split(' ')[1],
                                author_email = self.author_email, 
                                link = F"{subject_no_spaces}-{self.message_id}.html")
        logger.debug(F"subject_no_spaces: {subject_no_spaces}")
        return retval

class Blog:
    '''Class to have all blog entries'''
    def __init__(self):
        self.entries = []
        # self.read_entries_from_db()
    def generate_index(self):
        '''render the index'''
        rendered_blog_entries= []
        for entry in self.entries:
            rendered_blog_entries.append(entry.__str__())

        return "\n".join(rendered_blog_entries)

    def read_entries_from_db(self):
        '''read entries from database'''
        conn = sqlite3.connect(CONFIG.get('locations', 'database', fallback = None))
        conn.row_factory = dict_factory
        cur = conn.cursor()
        try:
            cur.execute('''select * from mail2blog order by date''')
            allentries = cur.fetchall()
            for entry in allentries:
                self.entries.append(Blog_entry.from_json(entry))
            # logging.info('Just read %d users' % len(allentries))
        except sqlite3.OperationalError as e:
            logging.error('SQL read error: %s' % str(e))
        except Exception as e:
            logging.error('Error: %s' % str(e))
            raise
        conn.close()


    def read_entries_from_imap(self, index=None, list_messages=False):
        '''read entries from database'''
        msg_list = imap.get_message_list()
        if index is not None:
            msg_list = [msg_list[index]]

        for msg in reversed(msg_list):
            # Decode as much as possible
            FIELDS = ['from', 'to', 'subject', 'date', 'Message-ID', 'Return-Path', 'Content-Type']
            dec_msg = {}
            for field in FIELDS:
                dec_msg[field] = tools.email_decode(msg[field])
            dec_msg['message-id']=msg['message-id'].replace('<','').replace('>','')
            if list_messages:
                print(F"{dec_msg['message-id']} | {dec_msg['from']} | {dec_msg['to']} |  {dec_msg['subject']}")
                # print(F"structure:\n  {_structure(msg)}")

            date = tools.dateparser(msg['date'])
            epoch = date.timestamp()
            self.entries.append(Blog_entry(message_id = dec_msg['message-id'],
                                           email_from = dec_msg['from'], 
                                           subject = dec_msg['subject'],
                                           epoch=epoch,
                                           source="imap"))
