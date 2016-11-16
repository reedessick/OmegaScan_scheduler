omegascan-configs:
	cd ligo-channel-lists && make omegascan
	cp ligo-channel-lists/*/*_omegascan.txt etc/
