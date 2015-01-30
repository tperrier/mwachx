#!/bin/bash

rm ../mwach/mwach.db
python ../manage.py migrate
python ../manage.py createsuperuser --username 'oscard' --email 'o@o.org'
python ./initial_import.py
