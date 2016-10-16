description = "parses OmegaScan config files, constructs associated output json objects, etc. Parsing inspired by https://github.com/ligovirgo/gwdetchar/blob/master/gwdetchar/omega/scan.py"
author      = "reed.essick@ligo.org"

#-------------------------------------------------

import os

from commands import gps2str

#-------------------------------------------------

def parseOmegaScanConfig( filename ):
    '''
    parses OmegaScan config file into a list of dictionaries.
    '''
    file_obj = open(filename, 'r')

    chans = []
    for line in file_obj:
        line = line.strip()

        if line and (line[0] == "{"): ### beginning of channel declaration
            chan = dict()

            line = file_obj.next().strip()
            while not line.endswith('}'): ### go until we hit the closing bracket
                key, val = line.split(':', 1) ### at most one split
                chan[key.strip()] = str2obj(val) ### assign parsed string to key

                line = file_obj.next().strip() ### bump iteration

            chans.append( chan )

    file_obj.close()

    return chans

def str2obj( val, warn=False ):
    '''
    converts strings to a variety of objects. 
    If the string is not understood, it is simply kept as a string unless warn=True. Then, a ValueError is raised.
    '''
    val = val.strip()
    if (val[0]=="'") and val.endswith("'"): ### normal string
        val = val.strip("'")

    elif (val[0]=='"') and val.endswith('"'): ### normal string
        val = val.strip("'")

    elif (val[0]=='[') and val.endswith(']'): ### a list of things
        val = [str2obj( v ) for v in val[1:-1].split()] ### assumes space-delimited

    else: ### probably an int or a float
        try:
            val = int(val)
        except:
            try:
                val = float(val)
            except:
                if warn:
                    raise ValueError('could not parse val=%s'%val)
    return val

def chan2url( chan, gps, outurl='./' ):
    '''
    map information about a single channel (format follows what's produced by parseOmegaScanConfig) into expected urls for the associated figures.

    NOTE: we modify the dictionary stored under 'chan' here!
    '''
    chanName  = chan['channelName']
    wins      = chan['plotTimeRanges']
    gps = gps2str(gps) ### standardizes how gps is passed -> how OmegaScans generate filenames

    ### add pointers to spectrograms, eventgrams, and timeseries
    ### NOTE: we actually modify the object and do NOT create a copy. We only add information, so this should be pretty safe
    chan.update( {'spectrogram' : dict((key, dict((win, os.path.join(outurl, "%s_%s_%.2f_spectrogram_%s.png"%(gps, chanName, win, key))) for win in wins)) for key in ['autoscaled', 'raw', 'whitened']),
                  'timeseries'  : dict((key, dict((win, os.path.join(outurl, "%s_%s_%.2f_timeseries_%s.png"%(gps, chanName, win, key)))  for win in wins)) for key in ['highpassed', 'raw', 'whitened']),
                  'eventgram'   : dict((key, dict((win, os.path.join(outurl, "%s_%s_%.2f_eventgram_%s.png"%(gps, chanName, win, key)))   for win in wins)) for key in ['autoscaled', 'raw', 'whitened']),
                 }
               )

    ### return the object
    return chan
