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

import gpxpy
import gpxpy.gpx

from mail2blog import logsetup
from mail2blog import tools 
from mail2blog.parse_args import args
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
        self.location         = None
        self.gpx_data         = None

        # Define locations
        blog_output_dir       = CONFIG.get('locations', 'blog_output')
        self.html_output_file = os.path.join(blog_output_dir, F"{self.subject}-{self.message_id}.html")
        temp_output_dir       = CONFIG.get('locations', 'temp_output')
        self.media_output_dir = os.path.join(temp_output_dir, F"{self.subject}-{self.message_id}")
        self.markdown         = ''
        self.gallery_name     = self.blog_entry.get_subject(replace_spaces=True) + '-' + self.blog_entry.get_message_id()
        self.gallery_icon     = None
        self.gallery_icon_basename = None

        # If the html file is already there, we don't need to re-render:
        if os.path.exists(self.html_output_file):
            if args.force:
                logger.info(F"{self.subject} already exists => removing article")
                os.remove(self.html_output_file)
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
        '''render:
            - md message via jinja to md
            - md to html 
            and write output'''
        # collect data:
        template_file     = CONFIG.get('templates', 'article')
        date              = self.blog_entry.date
        subject           = self.blog_entry.subject
        subject_no_spaces = self.blog_entry.get_subject(replace_spaces=True)
        author            = self.blog_entry.author
        author_email      = self.blog_entry.author_email
        message_id        = self.blog_entry.message_id
        
        # render template
        with open(template_file, 'r') as fh:
            template_data = fh.read()
        template = Template(template_data)

        markdown_data = template.render(date = date, 
                                subject = subject,
                                author = author,
                                author_first = author.split(' ')[0],
                                author_last  = author.split(' ')[1],
                                author_email = author_email, 
                                content = self.markdown,
                                link = F"{subject_no_spaces}-{self.message_id}.html")

        # if self.gpx_data:
        html_data = tools.render_pandoc_with_theme(markdown_data, title=subject,
                geolocation=self.location,
                gpx_data = self.gpx_data)

        logger.debug(F"saving html to {self.html_output_file}")
        with open(self.html_output_file, 'w') as fp:
            fp.write(html_data)
        os.chmod(self.html_output_file, 0o644)

    def render(self, maintype, *myargs, **mykwargs):
        if maintype == "text":
            return(self.text_renderer(*myargs, **mykwargs))
        if maintype == "image":
            return(self.image_renderer(*myargs, **mykwargs))
        if maintype == "video":
            return(self.video_renderer(*myargs, **mykwargs))
        return None

    def text_renderer(self, part):
        payload  = part.get_payload(decode=True)
        try:
            # [2021-07-20 22:30:25,917] { ...il2blog/database.py:83 }    INFO - loading message delme...
            # [2021-07-20 22:30:26,165] { ..../mail2blog/view.py:116}    INFO - content_maintype: text
            # [2021-07-20 22:30:26,165] { ..../mail2blog/view.py:118}    INFO - content_subtype: plain
            maintype = part.get_content_maintype()
            logger.info(F"content_maintype: {maintype}")
            subtype = part.get_content_subtype()
            logger.info(F"content_subtype: {subtype}")
            charset  = part.get_content_charset()
            logger.info(F"content_charset: {charset}")
        except Exception:
            pass

        # Handle gpx data:
        filename = part.get_filename()
        logger.debug(F"filename: {filename}")
        if filename is not None:
            extension = os.path.splitext(filename)[1] 
            logger.debug(F"extension: {extension}")
            if extension == ".gpx":
                temp = payload.decode('iso-8859-1')
                self.gpx_data = gpxpy.parse(temp)
                logger.debug("fine; stored gpx data")
                return None

        # Handle text body:
        self.markdown = payload.decode(charset)

        ## try to split off a potential header
        msg_body_parts = self.markdown.split('\n---')
        logger.debug(F"   len msg_body_parts: {len(msg_body_parts)}")
        self.markdown = msg_body_parts[-1]
        if len (msg_body_parts) > 1: # we have some kind of header
            ## copy the header into the local class
            msg_internal_header = msg_body_parts[0]
            logger.debug(F"internal header: {msg_internal_header}")
            parsed_header = tools.parse_internal_header(msg_internal_header)
            logger.debug(F"parsed header: {parsed_header}")
            supported_metadata = ['location', 'title', 'author']
            for metadata_item in supported_metadata:
                try:
                    setattr(self, metadata_item, parsed_header['location'])
                except KeyError:
                    pass

        ## Cut off footer
        try:
            self.markdown = self.markdown.split('\n-- ')[0]
        except Exception as e:
            logger.error(F"exception when trying to get rid of footer: {e}")
            # logger.error(F"actual markdown: {self.markdown}")


    def image_renderer(self, part):
        JPEG_EXTENSIONS=['JPG', 'JPEG', 'Jpeg', 'jpeg']
        tools.makepath(self.media_output_dir, 2)
        temp = part.get_filename()
        filename = re.sub(r"[\s+/]", '-', temp)
        for ext in JPEG_EXTENSIONS:
            filename = filename.replace(ext, 'jpg')
        logger.info(F"image: {filename}")
        actual_extension = filename.split('.')[-1]
        if actual_extension.lower() == 'png':
            logger.warning("PNG not yet supported by bic, skipping {filename}")
            return
        with open(os.path.join(self.media_output_dir  + '/' + filename), 'wb') as fp:
            fp.write(part.get_payload(decode=True))
        self.media_part_found = True
        self.gallery_icon_basename = os.path.basename(filename)
        logger.debug(F" gallery_icon_basename: {self.gallery_icon_basename }") 

    def video_renderer(self, part):
        tools.makepath(self.media_output_dir, 2)
        temp = part.get_filename()
        filename = re.sub(r"[\s+/]", '-', temp)
        logger.debug(F"video: {filename} -- Ignored")
        self.image_renderer(part)
        self.media_part_found = True

    def walker(self):
        for part in self.msg.walk():
            # print (F"message part: {part}")
            # charset  = part.get_content_charset()
            maintype = part.get_content_maintype()
            self.render(maintype, part)

    def _run_bic(self):
        bic = CONFIG.get('tools', 'bic') 
        # Works for ~marcus/public_html
        gallery_output = CONFIG.get('locations', 'gallery_output')
        gallery_link_base = CONFIG.get('locations', 'gallery_link_base') 
        tools.makepath(gallery_output)
        os.umask(0o022)

        logger.info(F"Generating gallery for {self.message_id}...")
        command = F'{bic} -i "{self.media_output_dir}" -n "{self.gallery_name}" -f -t any -r 0 -d {gallery_link_base} -o {gallery_output}> /dev/null 2>&1'
        logger.debug(F"gallery command: >>{command}<<")
        res = subprocess.call(command, shell = True)
        if res != 0:
            logger.error(F"Error when generating the gallery: {res}")
        self.gallery_icon = os.path.join(gallery_output, self.gallery_icon_basename)

    def _add_gallery_url(self):
        # FIXME: move this to template
        gallery_link_base = CONFIG.get('locations', 'gallery_link_base')
        gallery_link      = F"{gallery_link_base}/{self.gallery_name}"
        icon_url          = F"{gallery_link_base}/{self.gallery_name}/gallery/thumbs/{self.gallery_icon_basename}"
        self.markdown    += F"[![icon]({icon_url})]({gallery_link})"

def generate_index():
    blog=Blog()
    blog.read_entries_from_imap(args.message, args.list_messages)
    if args.list_messages:
        sys.exit(0)
    for entry in blog.entries:
        renderer=ArticleRenderer(entry)

    # blog_index_md   = blog.generate_index()
    blog_index_md   = blog.generate_index_new()
    blog_title = CONFIG.get('main', 'title', fallback='Blog')
    blog_index_html = tools.render_pandoc_with_theme(blog_index_md, title=blog_title)
    index_file_name = CONFIG.get('locations', 'blog_output') + "/index.html"


    tools.makepath(CONFIG.get('locations', 'blog_output'))
    with open(index_file_name, 'w') as fh:
        fh.write(blog_index_html)


if __name__ == '__main__':
    # sys.exit(main())
    sys.exit(generate_index())
