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

def condorOmegaScanCommand( exe, gps, exeConfig, frameDir, outdir, accounting_group, accounting_group_user, universe='vanilla' ):
    """
    returns cmd, stdout, stderr
        cmd    : a list of strings compatible with subprocess.Popen
        stdout : path to stdout (written in outdir)
        stderr : path to stderr (written in outdir)
    NOTE: command returned is for condor_submit_dag, not the actual OmegaScan. The actual OmegaScan command is wrapped within a sub file called from the dag.
    """

    raise NotImplementedError

    ### write sub file
    sub = "%s/%d.sub"%(outdir, gps)
    sub_obj = open(sub, 'w')
    sub_obj.write( '''universe = %(universe)s
executable = %(exe)s
arguments = "scan %(gps).9f -c %(exeConfig)s -f %(frameDir)s -o %(outdir) -r"
getenv = true
accounting_group = %(accounting_group)s
accounting_group_user = %(accounting_group_user)s
log    = %(outdir)s/%(gps)d-$(Cluster)-$(Process).log
error  = %(outdir)s/%(gps)d-$(Cluster)-$(Process).err 
output = %(outdir)s/%(gps)d-$(Cluster)-$(Process).out
notification = never
queue 1'''%{'universe':universe,
            'exe':exe,
            'gps':gps,
            'exeConfig':exeConfig,
            'framedir':frameDir,
            'outdir':outdir,
            'accounting_group':accounting_group,
            'accounting_group_user':accounting_group_user,
           } 
                 )
    sub_obj.close()

    ### write dag file
    dag = "%s/%d.dag"%(outdir, gps)
    dag_obj = open(dag, 'w')
    dag_obj.write( '''JOB %(gps)d %(sub)s
VARS %(gps)d
RETRY %(gps) %(retry)d'''%{'gps':gps, 
                           'sub':sub, 
                           'retry':retry,
                          } 
                 )
    dag_obj.close()

    ### set up command
    cmd = ['condor_submit_dag', dag]
    stdout = "%s/%d.out"%(outdir, gps)
    stderr = "%s/%d.err"%(outdir, gps)

    return cmd, stdout, stderr
