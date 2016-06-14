# OmegaScan_scheduler

a simple module that queries for data and launches OmegaScans in response to GraceDB events.

This can launch multiple OmegaScan processes. For each process, we need to know the frame type, the IFO, the amount of data needed, and possess a path to an OmegaScan config file.

We may also want to provide functionality to generate OmegaScan config files ``on the fly'' based on iDQ channel lists that are uploaded.
