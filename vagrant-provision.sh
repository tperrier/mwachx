#!/bin/bash

# This script expects the OS packages for python2, python virtualenv, nodejs, dos2unix, 
# and gcc-c++ and make are installed

MWACH_SOURCE_DIR="/vagrant"

npm install --global gulp-cli bower

cd $MWACH_SOURCE_DIR

# Windows doesn't support symlinks, so virtualbox/vagrant shared folders on a 
# Windows host does not, use --no-bin-links
bower install --allow-root
npm --no-bin-links install

# same deal with virtualenv and symlinks
virtualenv --always-copy mwachx-virtualenv

# use the virtualenv for the rest of the python stuff
source mwachx-virtualenv/bin/activate
pip install -r requirements.txt
echo "from .settings_base import *" > mwach/local_settings.py
dos2unix /vagrant/manage.py
python manage.py migrate
gulp buildonly
