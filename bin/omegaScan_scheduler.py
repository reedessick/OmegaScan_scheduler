#!/usr/bin/python
usage = "omegaScan_scheduler.py [--options] config.ini"
description = "schedules and forks OmegaScan processes"
author = "reed.essick@ligo.org"

#-------------------------------------------------

import sys
import json

import dataFind
import fork

from ligo.gracedb.rest import GraceDb

from ConfigParser import SafeConfigParser

from optparse import OptionParser

#-------------------------------------------------

parser = OptionParser(usage=usage, description=description)

parser.add_option('-v', '--verbose', default=False, action='store_true')
parser.add_option('-V', '--Verbose', default=False, action='store_true')

parser.add_option('-g', '--graceid', default=None, type='string', help='if supplied, generate scans for this event. Otherwise, we look in stdin for an alert.')

parser.add_option('-s', '--skip-upload', default=False, action='store_true', help='do not upload pointers to GraceDB')

opts, args = parser.parse_args()

if len(args) != 1:
    raise ValueError('please supply exactly one config file as an argument\n%s'%usage)
config_name = args[0]

opts.Verbose = opts.Verbose or opts.verbose

#-------------------------------------------------

### figure out event id
if opts.graceid==None:
    if opts.Verbose:
        print "reading lvalert message from stdin"
    alert = sys.stdin.read()
    if opts.Verbose:
        print "    %s"%(alert)
    alert = json.loads(alert)
    opts.graceid = alert['uid']

if opts.verbose:
    print "generating OmegaScans for : %s"%(opts.graceid)

#-------------------------------------------------

### load in config file
if opts.verbose:
    print "loading config file from : %s"%(config_name)
config = SafeConfigParser()
config.read( config_name )

raise NotImplementedError('figure out which chanset will need the least data -> order when they will be launched.')

#-------------------------------------------------

raise NotImplementedError('iterate through chansets: discover data and launch for each. Upload pointers to GraceDB')
