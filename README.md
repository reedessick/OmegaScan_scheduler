# OmegaScan_scheduler

a simple module that queries for data and launches OmegaScans in response to GraceDB events.

This can launch multiple OmegaScan processes. For each process, we need to know the frame type, the IFO, the amount of data needed, and possess a path to an OmegaScan config file.

---------------------------------------------------------------------

TODO:
 - implement ``on the fly'' functionality through a separate executable. Will need to automate writing OmegaScan config files, too.
 - improve job submission to condor. Allow tracking through dagman.out files so that `persist' can be used to track OmegaScan progress when submitting through condor. Currently, this is *not* supported.
 - need to automatically determine the correct url for links in GraceDB. Currently, we post a dummy link but we need to direct people to the correct url automatically.
