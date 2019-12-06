#!/bin/sh

./restart.sh
sudo service nginx restart
uwsgi --ini hydrology_mgmt_uwsgi.ini &