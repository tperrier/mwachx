#!/bin/bash

rm ../mwach/mwach.db
python ../manage.py migrate
python ./initial_import.py
