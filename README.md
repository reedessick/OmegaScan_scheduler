# OmegaScan_scheduler

a simple module that queries for data and launches OmegaScans in response to GraceDB events.

This can launch multiple OmegaScan processes. For each process, we need to know the frame type, the IFO, the amount of data needed, and possess a path to an OmegaScan config file.

---------------------------------------------------------------------

TODO:
 - implement ``on the fly'' functionality through a separate executable. Will need to automate writing OmegaScan config files, too.
 - improve job submission to condor. Allow tracking through dagman.out files so that `persist' can be used to track OmegaScan progress when submitting through condor. Currently, this is *not* supported.
 - improve error handling. Right now, if any individual bit fails the whole thing falls over. This means bad data from one IFO could kill the jobs for all IFOs. We may want to be a bit more graceful and just send or post a warning instead.
 - improve logging? Add time-stamps or just direct output into a consistent file?
