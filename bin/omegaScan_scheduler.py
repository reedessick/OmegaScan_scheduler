#!/usr/bin/python
usage       = "omegaScan_scheduler.py [--options] config.ini"
description = "schedules and forks OmegaScan processes"
author      = "reed.essick@ligo.org"

#-------------------------------------------------

import os
import sys
import json

import parse
import dataFind
import fork
import commands

import time
from lal.gpstime import tconvert

from ligo.gracedb.rest import GraceDb

from ConfigParser import SafeConfigParser

from optparse import OptionParser

#-------------------------------------------------

tagname = ['data_quality', 'OmegaScan'] ### these tags should always be applied when writing log messages

#-------------------------------------------------

parser = OptionParser(usage=usage, description=description)

parser.add_option('-v', '--verbose', default=False, action='store_true')
parser.add_option('-V', '--Verbose', default=False, action='store_true')

parser.add_option('-g', '--graceid', default=None, type='string', help='if supplied, generate scans for this event. Otherwise, we look in stdin for an alert.')

parser.add_option('-s', '--skip-upload', default=False, action='store_true', help='do not upload pointers to GraceDB')
parser.add_option('-r', '--robot-cert', default=False, action='store_true', help='set up robot certificate')

parser.add_option('-f', '--force', default=False, action='store_true', help='launch scans even if directory already exists or data is incomplete')

opts, args = parser.parse_args()

if len(args) != 1:
    raise ValueError('please supply exactly one config file as an argument\n%s'%usage)
config_name = args[0]

opts.verbose = opts.Verbose or opts.verbose
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
outurl      = config.get('general', 'outurl')
executable  = config.get('general', 'executable')

### figure out which chansets to process and in what order
chansets = config.get('general', 'chansets').split()
for chanset in chansets: ### ensure we have all the sections we need
    assert config.has_section(chanset), '%s has no section corresponding to chanset=%s'%(config_name, chanset)
chansets.sort(key=lambda chanset: config.getfloat(chanset, 'win')) ### extract windows for each chanset and order them accordingly

### whether to use condor
condor  = config.getboolean('general', 'condor')
if condor:
    universe              = config.get('condor', 'universe')
    accounting_group      = config.get('condor', 'accounting_group')
    accounting_group_user = config.get('condor', 'accounting_group_user')
    retry                 = config.getint('condor', 'retry')

### whether to stick around after forking processes
persist = config.getboolean('general', 'persist') \
            and upload_or_verbose \
            and (not condor)      ### a only persist if we will report somethin gnd we aren't submitting through condor

### FAR threshold to downselect events from GraceDB
farThr  = config.getfloat('general', 'farThr')

#-------------------------------------------------

### set up robot cert
if opts.robot_cert:
    if os.environ.has_key("X509_USER_PROXY"):
        del os.environ['X509_USER_PROXY']

    ### get cert and key from ini file
    os.environ['X509_USER_CERT'] = config.get('robot cert', 'robot_certificate')
    os.environ['X509_USER_KEY']  = config.get('robot cert', 'robot_key')

#-------------------------------------------------

### figure out event id
if opts.graceid==None:
    if opts.Verbose:
        print "reading lvalert message from stdin"
    alert = sys.stdin.read()

    if opts.Verbose:
        print "    %s"%(alert)
    alert = json.loads(alert)

    if alert['alert_type'] != 'new': ### ignore alerts that aren't new
        if opts.Verbose:
            print "ignoring alert"
        sys.exit(0)

    opts.graceid = alert['uid']

### extract things about the event
gdb = GraceDb( gracedb_url )
event = gdb.event( opts.graceid ).json()

gps = event['gpstime']
far = event['far']
if farThr < far:
    if opts.Verbose:
        print "ignoring alert due to high FAR (%.3e > %.3e)"%(far, farThr)
    sys.exit(0)

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
        gdb.writeLog( opts.graceid, message=message, tagname=tagname )

### set up frame directory
frmdir = os.path.join(outdir, opts.graceid, "frames")
if os.path.exists(frmdir):
    if not opts.force: ### ignore existing data if --force was supplied
        raise ValueError( "directory=%s already exists!"%(frmdir) )
else:
    os.makedirs( frmdir )

### iterate through chansets, processing each one separately
if persist:
    procs = []

for chanset in chansets:

    ### extract info about this chanset
    ifo        = config.get(chanset, 'ifo')
    exeConfig  = config.get(chanset, 'config')

    if opts.verbose:
        print "processing %s\n    ifo        : %s\n    config     : %s"%(chanset, ifo, exeConfig)

    ### parse exeConfig, get frame types, etc
    chans = parse.parseOmegaScanConfig( exeConfig )
    frametypes = set( chan['frameType'] for chan in chans )
    for frame_type in frametypes: ### ensure we have a section for each frame type
        assert config.has_section(frame_type), '%s has no section for frameType=%s'%(config_name, frame_type)

    ### figure out when to processes
    win    = config.getfloat(chanset, 'win')
    start  = gps-win
    end    = gps+win
    stride = 2*win

    ### wait until we have a chance of finding data (causality)
    wait = end - tconvert('now')
    if wait > 0:
        if opts.verbose:
            print "  waiting %.3f sec"%(wait)
        time.sleep( wait )

    #---------------------------------------------
    # DATA DISCOVERY
    #---------------------------------------------

    if opts.verbose:
        print "  finding frames"

    for frame_type in frametypes:

        lookup  = config.get(frame_type, 'lookup')
        timeout = end + config.getfloat(frame_type, 'timeout') ### add timeout to the end time

        if opts.verbose:
            print "    %s -> %s"%(frame_type, lookup)

        if lookup == 'ldr': ### find with LDR servers
            if config.has_option(frame_type, 'ldr-server'):
                ldr_server = config.get(frame_type, 'ldr-server')
            else:
                ldr_server = None
            ldr_url_type = config.get(frame_type, 'ldr-url-type')

            frames   = dataFind.ldr_find_frames( ldr_server, 
                                                 ldr_url_type, 
                                                 frame_type, 
                                                 ifo, 
                                                 start, 
                                                 stride, 
                                                 verbose=opts.Verbose 
                                               )
            coverage = dataFind.coverage(frames, start, stride)
            while (coverage < 1) and (tconvert('now')<timeout): ### still not enough coverage and we haven't timed out
                frames   = dataFind.ldr_find_frames( ldr_server, 
                                                     ldr_url_type, 
                                                     frame_type, 
                                                     ifo, 
                                                     start, 
                                                     stride, 
                                                     verbose=opts.Verbose 
                                                   )
                coverage = dataFind.coverage(frames, start, stride)

        elif lookup == 'shm': ### find directly from shared memory directory
            shm_dir  = config.get(frame_type, 'shm-dir')
            frames   = dataFind.shm_find_frames( shm_dir, 
                                                 ifo, 
                                                 frame_type, 
                                                 start, 
                                                 stride, 
                                                 verbose=opts.Verbose 
                                               )
            coverage = dataFind.coverage(frames, start, stride)
            while (coverage < 1) and (tconvert('now')<timeout):
                frames   = dataFind.shm_find_frames( shm_dir, 
                                                     ifo, 
                                                     frame_type, 
                                                     start, 
                                                     stride, 
                                                     verbose=opts.Verbose 
                                                   )
                coverage = dataFind.coverage(frames, start, stride)

        else:
            raise ValueError( 'lookup=%s not recognized!'%(lookup) )

        ### copy frames locally
        if coverage < 1: ### could not find enough coverage after timing out
            if upload_or_verbose:
                message = "could not find complete coverage for %s!\n%s"%(chanset, "\n".join(frames))
                if opts.verbose:
                    print message
                if opts.upload:
                    gdb.writeLog( opts.graceid, message=message, tagname=tagname )

            if not opts.force: ### we aren't forcing this scan, so we stop looking up data and move to the next chanset
                break

        if opts.verbose:
            print "  copying frames into local directory"
        newframes = ["%s/%s"%(frmdir, os.path.basename(frame)) for frame in frames]
        for frame, newframe in zip(frames, newframes):
            if opts.Verbose:
                print "    %s -> %s"%(frame, newframe)
            if not os.path.exists( newframe ): ### only copy if frame doesn't already exists
                fork.fork(['cp', frame, newframe]).wait() ### delegates to subprocess.Popen

    else: ### we did not break from the iteration over frametypes, so we want to actually run the scan

        #-----------------------------------------
        # SUBMIT COMMANDS
        #-----------------------------------------

        ### set up output directory and url
        this_outdir = os.path.join(outdir, opts.graceid, "scans", chanset.replace(" ",""))
        this_outurl = os.path.join(outurl, opts.graceid, "scans", chanset.replace(" ",""))
        if opts.verbose:
            print "  writing into : %s -> %s"%(this_outdir, this_outurl)

        if os.path.exists(this_outdir):
            if not opts.force: ### ignore existing data if --force was supplied
                raise ValueError( "directory=%s already exists!"%(this_outdir) )
        else:
            os.makedirs( this_outdir )

        ### submit execution command
        if condor: ### run under condor
            ### define execution command
            cmd, stdout, stderr = commands.condorOmegaScanCommand( executable,
                                                                   gps, 
                                                                   exeConfig, 
                                                                   frmdir, 
                                                                   this_outdir, 
                                                                   accounting_group, 
                                                                   accounting_group_user,
                                                                   universe=universe,
                                                                   retry=retry,
                                                                 )
            if opts.verbose:
                print "%s 1> %s 2> %s"%(" ".join(cmd), stdout, stderr)
            fork.safe_fork( cmd, stdout=stdout, stderr=stderr)

            ### report link to GraceDB for this chanset
            if upload_or_verbose:
                message = "OmegaScan process over %s within [%.3f, %.3f] started. Output can be found <a href=\"%s\">here</a>. WARNING: submitting through condor and will not track processes to ensure completion"%(chanset, start, end, this_outurl)
                if opts.verbose:
                    print message
                if opts.upload:
                    gdb.writeLog( opts.graceid, message=message, tagname=tagname )

        else: ### run on the head node
            ### define execution command
            cmd, stdout, stderr = commands.omegaScanCommand( executable, 
                                                             gps, 
                                                             exeConfig, 
                                                             frmdir, 
                                                             this_outdir 
                                                           )
            if opts.verbose:
                print "%s 1> %s 2> %s"%(" ".join(cmd), stdout, stderr)
            if persist: ### submit directly through subprocess and track proc
                proc = fork.fork( cmd, stdout=stdout, stderr=stderr )
                procs.append( (chanset, start, end, proc) )

                ### report link to GraceDB for this chanset
                ### because persist is True, we know that upload_or_verbose must also be True
                message = "OmegaScan process over %s within [%.3f, %.3f] started. Output can be found <a href=\"%s\">here</a>."%(chanset, start, end, this_outurl)
                if opts.verbose:
                    print message
                if opts.upload:
                    gdb.writeLog( opts.graceid, message=message, tagname=tagname )

            else: ### (double) fork and forget about proc
                fork.safe_fork( cmd, stdout=stdout, stderr=stderr)
    
                ### report link to GraceDB for this chanset
                if upload_or_verbose:
                    message = "OmegaScan process over %s within [%.3f, %.3f] started. Output can be found <a href=\"%s\">here</a>. WARNING: will not track processes to ensure completion"%(chanset, start, end, this_outurl)
                    if opts.verbose:
                        print message
                    if opts.upload:
                        gdb.writeLog( opts.graceid, message=message, tagname=tagname )

#-------------------------------------------------
# WAIT FOR COMMANDS TO FINISH, CLEAN UP
#-------------------------------------------------

if persist: ### wait around for all the processes to finish
    if opts.verbose:
        print "waiting for processes to finish"

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
                gdb.writeLog( opts.graceid, message=message, tagname=tagname )

        time.sleep( 1 ) ### wait one second between each check to ease the load on the cpu
            
### report to GraceDB that we've finished follow-up
if upload_or_verbose:
    message = "automatic OmegaScans finished."
    if condor or (not persist):
        message = message + " WARNING: not tracking actual OmegaScan processes and data may not be available immediately."
    if opts.verbose:
        print message
    if opts.upload:
        gdb.writeLog( opts.graceid, message=message, tagname=tagname )
