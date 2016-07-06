description = "a module that handles data discovery"

#-------------------------------------------------

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
    """
    end = start+stride

    frames = []
    for frame, (s, d) in [ (frame, extract_start_dur(frame, suffix=".gwf")) for frame in \
                             sorted(glob.glob("%s/%s1/%s-%s-*-*.gwf"%(directory, ifo, ifo, ldr_type))) ]:
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
