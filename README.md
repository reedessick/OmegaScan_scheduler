# OmegaScan_scheduler

a simple module that queries for data and launches OmegaScans in response to GraceDB events.

This can launch multiple OmegaScan processes. For each process, we need to know the frame type, the IFO, the amount of data needed, and possess a path to an OmegaScan config file. Multiple methods for data discovery are supported (read directly from /dev/shm/ or query through gw_data_find).

---------------------------------------------------------------------

# executables

  - bin/omegaScan_scheduler.py
    - The main scheduling script. This actually performs data discovery and formats the output directories, launching and managing child processes. Several submission modes are possible: 
        - submission through condor (currently does not allow tracking of spawned processes after submission)
        - submission to the local node (can either wait for processes to finish and ensure sucess or ``orphan'' them after forking)
    - Supports annotation within GraceDb using standard tags (hardcoded)

  - bin/is_lvalert_alive.sh
    - This shell script queries the process table to ensure that an instance of lvalert_listen with the appropriate command line options exists. If it does not, it re-launches the script and sends an email alert. is_lvalert_alive.sh is meant to be run periodically through cron, but can also be run by hand. An example cron command might be:

> * * * * * cd /home/detchar/opt/triggeredDQ/OmegaScanScheduler/ ; source ./setup.sh ; is_lvalert_alive.sh resource /home/detchar/opt/triggeredDQ/OmegaScanScheduler/etc/ER10-prod-la_lvalert-OmegaScanScheduler.ini /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/log/lvalert.out /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/log/lvalert.err "ressick@mit.edu" >> /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/is_lvalert_alive.log 2>> /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/is_lvalert_alive.log

# Config files

An example config file exists within the repo. Comments contained therein describe how to configure omegaScan_scheduler.py to run over multiple channel sets.

---------------------------------------------------------------------

# Installation and dependencies

This module depends on LALSuite (tconvert) and the GraceDb REST client. Both should be installed and managed by sysadmins on any LVC cluster. To ``install'' this package, simply clone the repo, enter the working directory and source ``./setup.sh''. This is a clunky way to update your path, and explains the first two commands in the example crontab above.

Users should be careful to build their own config files for both omegaScan_scheduler.py and lvalert_listen. However, examples are included in the repo and working versions of this module can be found under the detchar account at

> detchar.ligo-wa.caltech.edu:/home/detchar/opt/triggeredDQ/OmegaScanScheduler

with the appropriate substitution for LLO. These output to standard locations

 - lvalert_listen out and err
    - /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/log/lvalert.out
    - /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/log/lvalert.err
  - is_lvalert_alive.sh out and err
    - /home/detchar/opt/triggeredDQ/OmegaScanScheduler/etc/ER10-prod-wa_lvalert-OmegaScanScheduler.ini
  - omegaScan_scheduler.py out and err
    - /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/log/omegaScan_scheduler.out
    - /home/detchar/public_html/mon/triggeredDQ/OmegaScanScheduler/log/omegaScan_scheduler.err

and opperate on the following config files

  - lvalert_listen
    - /home/detchar/opt/triggeredDQ/OmegaScanScheduler/etc/ER10-prod-wa_lvalert-OmegaScanScheduler.ini
  - omegaScan_scheduler.py
    - /home/detchar/opt/triggeredDQ/OmegaScanScheduler/etc/ER10-prod-wa_OmegaScanScheduler.ini

---------------------------------------------------------------------

TODO:
 - implement ``on the fly'' functionality through a separate executable. Will need to automate writing OmegaScan config files, too.
 - improve job submission to condor. Allow tracking through dagman.out files so that `persist' can be used to track OmegaScan progress when submitting through condor. Currently, this is *not* supported.
 - improve logging? Add time-stamps or just direct output into a consistent file (current approach)?
