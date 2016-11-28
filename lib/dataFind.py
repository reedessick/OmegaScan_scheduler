description = "a module that handles data discovery"
author      = "reed.essick@ligo.org"

#-------------------------------------------------

import os
import glob
import subprocess as sp

#-------------------------------------------------

def ldr_find_frames(ldr_server, ldr_url_type, ldr_type, ifo, start, stride, verbose=False):
    """
    wrapper for ligo_data_find
    """
    end = start+stride

    if ldr_server:
        cmd = "gw_data_find --server=%s --url-type=%s --type=%s --observatory=%s --gps-start-time=%d --gps-end-time=%d"%(ldr_server, ldr_url_type, ldr_type, ifo, start, end)
    else:
        cmd = "gw_data_find --url-type=%s --type=%s --observatory=%s --gps-start-time=%d --gps-end-time=%d"%(ldr_url_type, ldr_type, ifo, start, end)

    if verbose:
        print cmd

    p = sp.Popen(cmd.split(), stdout=sp.PIPE, stderr=sp.STDOUT)

    frames = p.communicate()[0].replace("No files found!", "").replace("\n", " ") ### handle an empty list appropriately
    frames = frames.replace("file://localhost","")

    return [l for l in frames.split() if l.endswith(".gwf")]

def shm_find_frames(directory, ifo, ldr_type, start, stride, verbose=False):
    """
    searches for frames in directory assuming standard naming conventions.
    Does this by hand rather than relying on ldr tools

    specifically looks for the directory structure expected in /dev/shm buffers
    """
    end = start+stride

    globstring = "%s/%s1/%s-%s-*-*.gwf"%(directory, ifo, ifo, ldr_type)
    if verbose:
        print 'glob : '+globstring

    frames = []
    for frame, (s, d) in [ (frame, extract_start_dur(frame, suffix=".gwf")) for frame in \
                             sorted(glob.glob(globstring)) ]:
        if (s <= end) and (s+d >= start): ### there is some overlap!
            frames.append( frame )

    return frames

def arx_find_frames(directory, ifo, ldr_type, start, stride, verbose=False):
    """
    searches for frames in directory assuming standard naming convetions.
    Does this by hand rather than relying on ldr tools

    specifically looks for the directory structure expected in /archive/frames/ directories
    """
    end = start+stride

    startInt = int( start/1e5 ) ### needed for directory structure
    endInt   = int( end/1e5 )

    globstring = '%s/%s1/%s-%s-*'%(directory, ifo, ifo, ldr_type)
    if verbose:
        print 'glob : '+globstring

    frames = []
    for subdir in sorted(glob.glob(globstring)): ### walk through directories
        subInt = int( os.path.basename(subdir).split('-')[-1] )

        if (startInt <= subInt) and (subInt <= endInt): ### filter out only the interesting directories
            globstring = "%s/%s-%s-*-*.gwf"%(subdir, ifo, ldr_type)
            if verbose:
                print 'glob : '+globstring

            ### walk through files in this subdir
            for frame, (s, d) in [ (frame, extract_start_dur(frame, suffix=".gwf")) for frame in \
                             sorted(glob.glob(globstring)) ]:
                if (s <= end) and (s+d >= start): ### there is some overlap!
                    frames.append( frame )

    return frames


#-------------------------------------------------

def extract_start_dur(filename, suffix=".gwf"):
    return [int(l) for l in filename[:-len(suffix)].split("-")[-2:]]

def coverage(frames, start, stride):
    """
    determines the how much of [start, start+stride] is covered by these frames

    assumes non-overlapping frames!
    """
    ### generate segments from frame names
#    segs = [[float(l) for l in frame.strip(".gwf").split("-")[-2:]] for frame in sorted(frames)]
    segs = [extract_start_dur(frame) for frame in sorted(frames)]

    ### check whether segments overlap with desired time range
    covered = 1.0*stride

    end = start + stride
    for s, d in segs:
        e = s+d

        if (s < end) and (start < e): ### at least some overlap
            covered -= min(e, end) - max(s, start) ### subtract the overlap

            if covered <= 0:
                break

    return 1 - covered/stride ### return fraction of coverage

def gaps(frames, start, stride):
    """
    returns a list of gaps in coverage between [start, start+stride]

    assumes non-overlapping frames!
    """
    ### generate segments from frame names
    segs = [extract_start_dur(frame) for frame in sorted(frames)]

    if segs: ### non-empty list
        gaps = []
        end = segs[0][0]

        if start < end: ### gap at the beginning
            gaps.append( [start, end] ) 

        for s, d in segs: ### check for gaps in the middle
            if s+d < start: ### too early; we don't care
                end = s+d 

            elif s > start+stride: ### too late, we don't care
                break

            elif s==end: ### no gap
                end += d

            else: ### there is a gap
                gaps.append( [end, s] )
                end = s+d

        if end < start+stride: ### gap at the end
            gaps.append( [end, start+stride] )                

    else: ### segs is empty
        gaps = [ [start, start+stride] ]

    return gaps
