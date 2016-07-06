description = "a module that forks subprocesses in a safe manner that does not leave zombie proc's"

#-------------------------------------------------

import subprocess as sp
import multiprocessing as mp

#------------------------------------------------

def fork(cmd, stdin=None, stdout=None, stderr=None):
    """
    helper for a double fork. This is called by multiprocessing to orphan the actual processes
    can also be called directly
    """
    if stdin:
        stdin_obj = open(stdin, "r")
    if stdout:
        stdout_obj = open(stdout, "w")
    if stderr:
        stderr_obj = open(stderr, "w")

    if stdin and stdout and stderr:
        p = sp.Popen(cmd, stdin=stdin_obj, stdout=stdout_obj, stderr=stderr_obj) ### launch subprocess
                ### we don't wait, communicate or call
                ### by returning, this process will die and orphan the subprocess
    elif stdin and stdout:
        p = sp.Popen(cmd, stdin=stdin_obj, stdout=stdout_obj)
    elif stdin and stderr:
        p = sp.Popen(cmd, stdin=stdin_obj, stderr=stderr_obj)
    elif stdout and stderr:
        p = sp.Popen(cmd, stdout=stdout_obj, stderr=stderr_obj)
    elif stdin:
        p = sp.Popen(cmd, stdin=stdin_obj)
    elif stdout:
        p = sp.Popen(cmd, stdout=stdout_obj)
    elif stderr:
        p = sp.Popen(cmd, stderr=stderr_obj)
    else:
        p = sp.Popen(cmd)

    if stdin:
        stdin_obj.close()
    if stdout:
        stdout_obj.close()
    if stderr:
        stderr_obj.close()

    return p

###
def safe_fork(cmd, stdin=None, stdout=None, stderr=None):
        """
        a wrapper for a double fork
        """
        p = mp.Process(target=fork, args=(cmd, stdin, stdout, stderr)) ### define job
        p.start() ### launch
        p.join() ### call, will orphan subprocess when it finishes
