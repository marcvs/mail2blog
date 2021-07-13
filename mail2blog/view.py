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
import mimetypes
import pypandoc
import subprocess

from mail2blog import logsetup
from mail2blog import tools 
from mail2blog.config import CONFIG
from mail2blog.database import Blog_entry, Blog

logger = logging.getLogger(__name__)

class ArticleRenderer():
    '''Methods for rendering various mime types'''
    def __init__(self, blog_entry):
        self.blog_entry       = blog_entry
        self.message_id       = blog_entry.get_message_id()
        self.subject          = blog_entry.get_subject(replace_spaces=True)
        self.media_part_found = False

        # Define locations
        blog_output_dir       = CONFIG.get('locations', 'blog_output')
        self.html_output_file = os.path.join(blog_output_dir, F"{self.subject}-{self.message_id}.html")
        temp_output_dir       = CONFIG.get('locations', 'temp_output')
        self.media_output_dir = os.path.join(temp_output_dir, F"{self.subject}-{self.message_id}")

        # If the html file is already there, we don't need to re-render:
        if os.path.exists(self.html_output_file):
            logger.info(F"{self.html_output_file} already exists => skipping article")

        else:
            self.msg          = blog_entry.get_message()

            tools.makepath(blog_output_dir, 2)
            tools.makepath(self.media_output_dir, 2)

            self.text = None
            self.media = []

            self.walker()
            if self.media_part_found:
                self._run_bic()

    def render(self, maintype, *args, **kwargs):
        if maintype == "text":
            return(self.text_renderer(*args, **kwargs))
        if maintype == "image":
            return(self.image_renderer(*args, **kwargs))
        if maintype == "video":
            return(self.video_renderer(*args, **kwargs))
        return None

    def text_renderer(self, part):
        prt = part.get_payload(decode=True)
        inpt = prt.decode('iso-8859-1')
        inpt = inpt.split('\n-- \n')[0]
        style_file_name = CONFIG.get('themes', 'style_file', fallback=None) 
        with open(style_file_name, 'r') as st:
            style = st.read()

        html_data = pypandoc.convert_text(style + inpt, 'html', format='md')

        with open(self.html_output_file, 'w') as fp:
            fp.write(html_data)

    def image_renderer(self, part):
        # self.media.append(part.get_payload(decode=True))

        filename = part.get_filename()
        logger.debug(F"image: {filename}")
        with open(os.path.join(self.media_output_dir  + '/' + filename), 'wb') as fp:
            fp.write(part.get_payload(decode=True))
        self.media_part_found = True

    def video_renderer(self, part):
        filename = part.get_filename()
        logger.debug(F"video: {filename} -- Ignored")
        self.image_renderer(part)
        self.media_part_found = True

    def walker(self):
        for part in self.msg.walk():
            maintype =  part.get_content_maintype()
            self.render(maintype, part)

    def _run_bic(self):
        bic = CONFIG.get('tools', 'bic') 
        # Works for ~marcus/public_html
        gallery_name = self.blog_entry.get_subject(replace_spaces=True)
        gallery_output = CONFIG.get('locations', 'gallery_output')
        tools.makepath(gallery_output)

        command = F'{bic} -i "{self.media_output_dir}" -n "{gallery_name}" -f -t any -r 0 -d /nordkapp/pix -o {gallery_output}> /dev/null 2>&1'
        logger.debug(F"bic command: >>{command}<<")
        res = subprocess.call(command, shell = True)
        print("Returned Value: ", res)

        # FIXME: Copy / move output to ~/public_html/blogs/nordkapp/pix/subject
        # Or point self.media_output_dir to that directory

def generate_index():
    blog=Blog()
    blog.read_entries_from_imap()
    # blog.read_entries_from_db()
    print ("generating view:")
    print(blog.__str__())
    # sys.exit(0)
    for entry in blog.entries:
        # FIXME: check if output is already created
        renderer=ArticleRenderer(entry)

if __name__ == '__main__':
    # sys.exit(main())
    sys.exit(generate_index())
