# OmegaScan_scheduler

a simple module that queries for data and launches OmegaScans in response to GraceDB events.

This can launch multiple OmegaScan processes. For each process, we need to know the frame type, the IFO, the amount of data needed, and possess a path to an OmegaScan config file.

We may also want to provide functionality to generate OmegaScan config files ``on the fly'' based on iDQ channel lists that are uploaded.

---------------------------------------------------------------------

TODO:
 -- implement ``on the fly'' functionality through a separate executable. Will need to automate writing OmegaScan config files, too.
 -- implement job submission to condor. This should be straightforward to implement under commands.py with existing infrastructure, but automating the dag and sub writting deserves some thought.
