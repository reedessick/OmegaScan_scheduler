#!/usr/bin/python
usage = "omegaScan_scheduler.py [--options] config.ini"
description = "schedules and forks OmegaScan processes"
author = "reed.essick@ligo.org"

#-------------------------------------------------

import os
import sys
import json

import dataFind
import fork

import time
from lal.gpstime import tconvert

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
opts.upload  = not opts.skip_upload ### do this once so we don't repeat it over and over

upload_or_verbose = opts.upload or opts.verbose

#-------------------------------------------------

### load in config file
if opts.verbose:
    print "loading config file from : %s"%(config_name)
config = SafeConfigParser()
config.read( config_name )

### pull out general info
gracedb_url = config.get('general', 'gracedb-url')
outdir      = config.get('general', 'outdir')
executable  = config.get('general', 'executable')

chansets = config.get('general', 'chansets').split()
chansets.sort(key=lambda chanset: config.getfloat(chanset, 'win')) ### extract windows for each chanset and order them accordingly

persist = config.getbool('general', 'persist') and upload_or_verbose ### we only persist if we will report something

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

### extract things about the event
gdb = GraceDb(gracedb_url)
gps = json.loads(gdb.event(opts.graceid).read())['gpstime']

if opts.verbose:
    print "generating OmegaScans for : %s\n    gps : %.6f"%(opts.graceid, gps)

#-------------------------------------------------

### report to GraceDB that we've started follow-up
if upload_or_verbose:
    message = "automatic OmegaScans begun for: %s."%(", ".join(chansets))
    if not persist:
        message = message + " WARNING: we will not track the individual OmegaScan processes to ensure completion"

    if opts.verbose:
        print message
    if opts.upload:
        gdb.writeLog( opts.graceid, message=message, tagname=['data_quality'] )

### iterate through chansets, processing each one separately
if persist:
    proc = []

for chanset in chansets:

    ### extract info about this chanset
    ifo        = config.get(chanset, 'ifo')
    frame_type = config.get(chanset, 'frame_type')
    exeConfig  = config.get(chanset, 'config')

    if opts.verbose:
        print "processing %s\n    ifo        : %s\n    frame_type : %s\n    config      : %s"%(chanset, ifo, frame_type, exeConfig)

    ### set up output directory
    this_outdir = os.path.join(outdir, opts.graceid, chanset.replace(" ",""))
    if opts.verbose:    
        print "  writing into : %s"%(this_outdir)

    if os.path.exists(this_outdir):
        raise ValueError( "directory=%s already exists!"%(this_outdir) )
    else:
        os.path.makedirs( this_outdir )

    ### figure out when to processes
    win    = config.getfloat(chanset, 'win')
    start  = gps-win
    end    = gps+win
    stride = 2*win

    ### go find data
    lookup  = config.get(chanset, 'lookup')
    timeout = end + config.getfloat(chanset, 'timeout') ### add timeout to the end time

    ### wait until we have a chance of finding data (causality)
    wait = end - tconvert(now)
    if wait > 0:
        if opts.verbose:
            print "  waiting %.3f sec"%(wait)
        time.sleep( wait )

    frames = []
    coverage = 0
    if opts.verbose:
        print "  finding frames"
    if lookup == 'ldr': ### find with LDR servers
        ldr_server   = config.get(chanset, 'ldr_server')
        ldr_url_type = config.get(chanset, 'ldr_url_type')
        while (coverage < 1) and (tconvert(now)<timeout):
            frames = dataFind.ldr_find_frames( ldr_server, ldr_url_type, frame_type, ifo, start, stride, verbose=opts.Verbose )
            coverage = dataFind.coverage(frames, start, stride)

    elif lookup == 'shm': ### find directly from shared memory directory
        shm_dir = config.get(chanset, 'shm_dir')
        while (coverage < 1) and (tconvert(now)<timeout):
            frames = dataFind.shm_find_frames( shm_dir, ifo, frame_type, start, stride, verbose=opts.Verbose )
            coverage = dataFind.coverage(frames, start, stride)

    else:
        raise ValueError( 'lookup=%s not recognized!'%(lookup) )

    if coverage < 1:
        raise ValueError( 'could not find complete coverage!\n%s'%("\n".join(frames)) )

    ### copy frames into a local directory
    if opts.verbose:
        print "  copying frames into local directory"
    newframes = ["%s/%s"%(this_outdir, os.path.basename(frame)) for frame in frames]
    for frame, newframe in zip(frames, newframes):
        sp.Popen(['cp', frame, newframe]).wait()

    ### define execution command
    cmd, stdout, stderr = commands.omegaScanCommand( executable, exeConfig, this_outdir, this_outdir )
    if opts.verbose:
        print "%s 1> %s 2> %s"%(" ".join(cmd), stdout, stderr)

    output_url = "FIXME: output_url"

    ### submit execution command
    if persist: ### submit directly through subprocess and track proc
        stdout_obj = open(stdout, 'w')
        stderr_obj = open(stderr, 'w')
        proc = sp.Popen(cmd, stdout=stdout_obj, stderr=stderr_obj)
        stdout_obj.close()
        stderr_obj.close() 
        procs.append( (chanset, start, end, proc) )

        ### report link to GraceDB for this chanset
        ### because persist is True, we know that upload_or_verbose must also be True
        message = "OmegaScan process over %s within [%.3f, %.3f] started. Output can be found <a href=\"%s\">here</a>."%(chanset, start, end, link, output_url)
        if opts.verbose:
            print message
        if opts.verbose:
            gdb.writeLog( opts.graceid, message=message, tagname=['data_quality'] )

    else: ### (double) fork and forget about proc
        fork.safe_fork( cmd, stdout=stdout, stderr=stderr)

        ### report link to GraceDB for this chanset
        if opts.verbose or opts.upload:
            message = "OmegaScan process over %s within [%.3f, %.3f] started. Output can be found <a href=\"%s\">here</a>. WARNING: will not track processes to ensure completion"%(chanset, start, end, output_url)
            if opts.verbose:
                print message
            if opts.upload:
                gdb.writeLog( opts.graceid, message=message, tagname=['data_quality'] )

if persist: ### wait around for all the processes to finish
    while len(procs):
        chanset, start, end, proc = procs.pop(0) ### get the first proc
        returncode = proc.poll()

        if returncode==None: ### proc has not finished
            procs.append( (chanset, start, end, proc) ) ### add to the back of the list

        else: ### proc has finished
            if returncode!=0:
                message = "WARNING: OmegaScan over %s within [%.3f, %.3f] finished with returncode=%d"%(chanset, start, end, returncode)
            else:
                message = "OmegaScan over %s within [%.3f, %.3f] finished"%(chanset, start, end)
            if opts.verbose:
                print message
            if opts.upload:
                gdb.writeLog( opts.graceid, message=message, tagname=['data_quality'] )
            
### report to GraceDB that we've finished follow-up
if upload_or_verbose:
    message = "automatic OmegaScans finished"
    if opts.verbose:
        print message
    if opts.upload:
        gdb.writeLog( opts.graceid, message=message, tagname=['data_quality'] )
