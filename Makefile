omegascan-configs:
	git submodule init
	git submodule update
	cd ligo-channel-lists && git pull origin HEAD:master && for INI in `ls */*ini` ; do OUT=$$(echo $${INI} | sed -e s/.ini/_omegascan.txt/) ; echo "converting $${INI} to $${OUT}" ; tools/clf-to-omegascan.py -f -o $${OUT} $${INI} --always-plot; done
	mv ligo-channel-lists/*/*_omegascan.txt etc/
	for cnf in etc/*_omegascan.txt ; do sed -i -e s,HOFT_C00,llhoft, $${cnf} ; done
