#!/bin/bash

cd /vagrant

# Windows doesn't support symlinks, so virtualbox/vagrant shared folders on a 
# Windows host does not, use --no-bin-links
echo "npm --no-bin-links install"
npm --no-bin-links install

# same deal with virtualenv and symlinks
echo "virtualenv --always-copy mwachx-virtualenv"
virtualenv --always-copy mwachx-virtualenv
echo "source mwachx-virtualenv/bin/activate"
source mwachx-virtualenv/bin/activate
echo "pip install -r requirements.txt"
pip install -r requirements.txt
echo "from .settings_base import *" > mwach/local_settings.py
dos2unix /vagrant/manage.py
echo "/usr/bin/python manage.py migrate"
/usr/bin/python /vagrant/manage.py migrate


