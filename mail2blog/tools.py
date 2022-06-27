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
import logging

logger = logging.getLogger(__name__)

from mail2blog.config import CONFIG


def makepath(directory, depth=3):
    basepath = "/".join(directory.split("/")[0:-depth])
    snippets = directory.split("/")[-depth:]

    paths = []
    for i in range(0, len(snippets)):
        paths.append(basepath + "/" + "/".join(snippets[0 : i + 1]))

    for path in paths:
        logger.debug(F"making: {path}")
        try:
            os.mkdir(path)
            os.chmod(path, 0o755)
        except FileExistsError as e:
            # logger.warning(F"Cannot create directory: {e}")
            pass


def email_decode(value):
    """Decode email encoding"""
    return email.header.make_header(email.header.decode_header(value))


def dateparser(text):
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%m/%d/%y %H:%M",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            # epoch = date.timestamp()
            return datetime.strptime(text, fmt).timestamp()
        except ValueError:
            pass
    raise ValueError(f"no valid date format found: >>{text}<<")


# >>Tue, 13 Jul 2021 10:52:08 +0200<<
def render_pandoc_with_geolocation(
        inpt, title="Title", gpx_data: dict = {}, geolocation: list = []
):
    temp_dir = CONFIG.get("locations", "temp_output", fallback="/tmp")
    header_include_file = CONFIG.get("themes", "header_include", fallback=None)
    body_after_include_file = os.path.join(temp_dir, "geo.tmp")
    body_before_include_file = CONFIG.get(
        "themes", "body_before_include", fallback=None
    )
    map_view= CONFIG.get("map", "map_view", fallback="[45.00, 9.49], 7")
    geo_data = f"""
        </article>

        <script>
            var mymap = L.map('mapid').setView({map_view});
            L.tileLayer('https://api.mapbox.com/styles/v1/{{id}}/tiles/{{z}}/{{x}}/{{y}}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {{
                maxZoom: 18,
                attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
                    'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
                id: 'mapbox/streets-v11',
                tileSize: 512,
                zoomOffset: -1
            }}).addTo(mymap);
        </script>"""

    if geolocation:
        logger.debug(f"got geolocation: {geolocation}")
        lat = geolocation[0]
        lon = geolocation[1]
        geo_data += f"""
            <script>
            <!--geolocation-->
            var marker = L.marker([{lat}, {lon}]).addTo(mymap);
            <!--geolocation-->
            </script>"""
        # geo_data += F'''
        #     <script>
        #     <!--geolocation-->
        #     var circle = L.circle([{lat}, {lon}], {{
        #         color: 'red',
        #         fillColor: '#f03',
        #         fillOpacity: 0.5,
        #         radius: 100
        #     }}).addTo(mymap);
        #     <!--geolocation-->
        #     </script>'''
    if gpx_data:
        logger.debug(f"got gpx_data")

        geo_data += """
            <script>
            <!--gpx_data-->
            var latlngs = [
            """
        is_first = True
        for track in gpx_data.tracks:
            for segment in track.segments:
                # print("new segment")
                for point in segment.points:
                    if not is_first:
                        geo_data += ",\n"
                    if is_first:
                        is_first = False
                    geo_data += f"[{point.latitude}, {point.longitude}]"

        geo_data += """
            ];
            var polyline = L.polyline(latlngs, {color: 'red'}).addTo(mymap);
            <!--gpx_data-->
            </script>
            """
        # var latlngs = [
        #     [45.51, -122.68],
        #     [37.77, -122.43],
        #     [34.04, -118.2]
        # ];
        #
        # var polyline = L.polyline(latlngs, {color: 'red'}).addTo(map);

    logger.debug(f"Writing to {body_after_include_file}")
    with open(body_after_include_file, "w") as tf:
        tf.write(geo_data)
        logger.debug(f"wrote to {body_after_include_file}")

    pandoc_args = [
        "-s",
        f"--metadata=title:{title}",
        f"--include-in-header={header_include_file}",
        f"--include-before-body={body_before_include_file}",
        f"--include-after-body={body_after_include_file}",
    ]
    logger.debug(f"pandoc args: {pandoc_args}")
    # header = F'title: {title}\n---\n'
    html_data = pypandoc.convert_text(inpt, "html", format="md", extra_args=pandoc_args)
    return html_data


def render_pandoc_with_theme(inpt, title="Title", gpx_data=False, geolocation=False):
    if geolocation or gpx_data:
        return render_pandoc_with_geolocation(inpt, title, gpx_data, geolocation)

    header_include_file = CONFIG.get("themes", "header_include_no_map", fallback=None)
    body_after_include_file = CONFIG.get(
        "themes", "body_after_include_no_map", fallback=None
    )
    body_before_include_file = CONFIG.get(
        "themes", "body_before_include_no_map", fallback=None
    )

    pandoc_args = [
        "-s",
        f"--metadata=title:{title}",
        f"--include-in-header={header_include_file}",
        f"--include-before-body={body_before_include_file}",
        f"--include-after-body={body_after_include_file}",
    ]
    logger.debug(f"pandoc args: {pandoc_args}")
    # header = F'title: {title}\n---\n'
    html_data = pypandoc.convert_text(inpt, "html", format="md", extra_args=pandoc_args)
    return html_data


def htmlescape(text):
    """escape html characters"""
    d = dict(
        (chr(code), "&%s;" % name)
        for code, name in codepoint2name.items()
        if code != 38
    )  # exclude "&"
    if "&" in text:
        text = text.replace("&", "&amp;")
    for key, value in d.items():
        if key in text:
            text = text.replace(key, value)
    return text


def parse_internal_header(header):
    retval = {}
    for line in header.split("\n"):
        logger.debug(f"  header line: {line}")
        try:
            colonseparated = line.split(":")
            key = colonseparated[0]
            values = [v.rstrip().lstrip() for v in colonseparated[1:]]
            logger.debug(f"           key: {key} -- {values}")
            retval[key] = values
        except Exception as e:
            logger.warning(f"Trouble when parsing header: {e}")
    return retval


def decode_message(msg):
    """Decode as much as possible"""
    FIELDS = [
        "from",
        "to",
        "subject",
        "date",
        "Message-ID",
        "Return-Path",
        "Content-Type",
    ]
    dec_msg = {}
    for field in FIELDS:
        dec_msg[field] = email_decode(msg[field])
    dec_msg["message-id"] = msg["message-id"].replace("<", "").replace(">", "")
    return dec_msg
