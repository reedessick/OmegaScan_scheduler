omegascan-configs:
	cd ligo-channel-lists && make omegascan
	mv ligo-channel-lists/*/*_omegascan.txt etc/
