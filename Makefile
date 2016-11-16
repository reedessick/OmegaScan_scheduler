omegascan-configs:
	cd ligo-channel-lists && git pull origin HEAD:master && make omegascan
	mv ligo-channel-lists/*/*_omegascan.txt etc/
