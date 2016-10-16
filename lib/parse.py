description = "parses OmegaScan config files, constructs associated output json objects, etc. Parsing inspired by https://github.com/ligovirgo/gwdetchar/blob/master/gwdetchar/omega/scan.py"
author      = "reed.essick@ligo.org"

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
