#!/bin/bash

if [ ! -d /opt ]; then
	mkdir /opt
fi
if [ ! -d /opt/keezer_client ]; then
	mkdir /opt/keezer_client
fi
if [ ! -d /var/opt/keezer_client ]; then
	mkdir /var/opt/keezer_client
fi

if [ ! -f /etc/opt/keezer_client.cfg ]; then
	cp ./keezer_client.cfg.example /etc/opt/keezer_client.cfg 
fi
cp ./keezer_client.py /opt/keezer_client/keezer_client.py
apt-get install -y python python-rpi.gpio 
curl https://bootstrap.pypa.io/get-pip.py | sudo python
pip install -r ./requirements.txt
cp ./keezer_client.service /lib/systemd/system/keezer_client.service
chmod 644 /lib/systemd/system/keezer_client.service
systemctl daemon-reload
systemctl enable keezer_client.service
