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
import sys
import argparse
import logging
import gpxpy
import gpxpy.gpx

logger = logging.getLogger(__name__)


def parseOptions():
    '''Parse the commandline options'''
    folder_of_executable = os.path.split(sys.argv[0])[0]
    parser = argparse.ArgumentParser(description='''reduce-gpx''')
    parser.add_argument('--input',  '--in',  '-i',      default=None)
    parser.add_argument('--output', '--out', '-o',      default=None)
    parser.add_argument('--interval', '--int', '-t',    default=60, type=int)
    parser.add_argument('--debug',    '-d',             default=False, action="store_true")
    parser.add_argument('--verbose',  '-v',             default=False, action="store_true")
    args = parser.parse_args()
    return args

# reparse args on import
args = parseOptions()


# Creating a new file:
# --------------------
r_gpx = gpxpy.gpx.GPX()

# Create first track in our GPX:
r_gpx_track = gpxpy.gpx.GPXTrack()
r_gpx.tracks.append(r_gpx_track)

# Create first segment in our GPX track:
r_gpx_segment = gpxpy.gpx.GPXTrackSegment()
r_gpx_track.segments.append(r_gpx_segment)

# Create points:
# r_gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(2.1234, 5.1234, elevation=1234))


# Parsing an existing file:
# -------------------------
if args.input is None:
    print("Error: must use --in or -i to specify input file")
    sys.exit(1)
if args.output is None:
    args.output = os.path.splitext(args.input)[0] + '-reduced' + ospath.splitext(args.input)[1]

gpx_file = open(args.input, 'r')
r_gpx_file = open(args.output, 'w')

gpx = gpxpy.parse(gpx_file)

last_time = gpx.tracks[0].segments[0].points[0].time
for track in gpx.tracks:
    for segment in track.segments:
        # print("new segment")
        for point in segment.points:
            timedelta = point.time - last_time
            # print (F"timedelta: {last_time}")
            if (timedelta.total_seconds()) > args.interval:
                last_time = point.time
                r_gpx_segment.points.append(point)


# for waypoint in gpx.waypoints:
#     print('waypoint {0} -> ({1},{2})'.format(waypoint.name, waypoint.latitude, waypoint.longitude))
#
# for route in gpx.routes:
#     print('Route:')
#     for point in route.points:
#         print('Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation))

r_gpx_file.write(r_gpx.to_xml())


