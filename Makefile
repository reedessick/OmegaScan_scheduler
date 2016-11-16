omegascan-configs:
	git submodule init
	git submodule update
	cd ligo-channel-lists && git pull origin HEAD:master && make omegascan
	mv ligo-channel-lists/*/*_omegascan.txt etc/
