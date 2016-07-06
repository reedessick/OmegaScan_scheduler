description = "a module that builds command lines for OmegaScan processes"

#-------------------------------------------------

def omegaScanCommand( exe, gps, exeConfig, frameDir, outdir ):
    """
    returns cmd, stdout, stderr
        cmd    : a list of strings compatible with subprocess.Popen
        stdout : path to stdout (written in outdir)
        stderr : path to stderr (written in outdir)
    """
    cmd = [exe, 'scan', "%.9f"%(gps), '-c', exeConfig, '-f', frameDir, '-o', outdir, '-r']
    stdout = "%s/%d.out"%(outdir, gps)
    stderr = "%s/%d.err"%(outdir, gps)

    return cmd, stdout, stderr
