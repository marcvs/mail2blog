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
        self.markdown         = ''

        # If the html file is already there, we don't need to re-render:
        if os.path.exists(self.html_output_file):
            logger.info(F"{self.subject} already exists => skipping article")

        else:
            self.msg          = blog_entry.get_message()

            tools.makepath(blog_output_dir, 2)

            self.text = None
            self.media = []

            self.walker()
            if self.media_part_found:
                self._run_bic()
                self._add_gallery_url()
            self.write_output()

    def write_output(self):
        '''render md to html and write output'''
        html_data = tools.render_pandoc_with_theme(self.markdown)
        logger.debug(F"saving html to {self.html_output_file}")
        with open(self.html_output_file, 'w') as fp:
            fp.write(html_data)

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
        self.markdown = prt.decode('iso-8859-1')
        self.markdown = self.markdown.split('\n-- ')[0]
    def image_renderer(self, part):
        JPEG_EXTENSIONS=['JPG', 'JPEG', 'Jpeg', 'jpeg']
        tools.makepath(self.media_output_dir, 2)
        temp = part.get_filename()
        filename = re.sub(r"[\s+/]", '-', temp)
        for ext in JPEG_EXTENSIONS:
            filename = filename.replace(ext, 'jpg')
        logger.info(F"image: {filename}")
        with open(os.path.join(self.media_output_dir  + '/' + filename), 'wb') as fp:
            fp.write(part.get_payload(decode=True))
        self.media_part_found = True

    def video_renderer(self, part):
        tools.makepath(self.media_output_dir, 2)
        temp = part.get_filename()
        filename = re.sub(r"[\s+/]", '-', temp)
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
        gallery_output = CONFIG.get('locations', 'gallery_output')
        gallery_link_base = CONFIG.get('locations', 'gallery_link_base') 
        gallery_name = self.blog_entry.get_subject(replace_spaces=True)
        tools.makepath(gallery_output)

        logger.info(F"Generating gallery for {self.message_id}...")
        command = F'{bic} -i "{self.media_output_dir}" -n "{gallery_name}" -f -t any -r 0 -d {gallery_link_base} -o {gallery_output}> /dev/null 2>&1'
        logger.debug(F"gallery command: >>{command}<<")
        res = subprocess.call(command, shell = True)
        if res != 0:
            logger.error(F"Error when generating the gallery: {res}")

    def _add_gallery_url(self):
        gallery_link_base = CONFIG.get('locations', 'gallery_link_base') 
        gallery_name = self.blog_entry.get_subject(replace_spaces=True)
        self.markdown += F"\n[Bilder]({gallery_link_base}/{gallery_name})"

def generate_index():
    blog=Blog()
    blog.read_entries_from_imap()
    # sys.exit(0)
    for entry in blog.entries:
        renderer=ArticleRenderer(entry)

    blog_index_md = blog.generate_index()

    blog_index_html = tools.render_pandoc_with_theme(blog_index_md)
    # FIXME: index.html
    index_file_name = CONFIG.get('locations', 'blog_output') + "/test.html"

    tools.makepath(CONFIG.get('locations', 'blog_output'))
    with open(index_file_name, 'w') as fh:
        fh.write(blog_index_html)


if __name__ == '__main__':
    # sys.exit(main())
    sys.exit(generate_index())
