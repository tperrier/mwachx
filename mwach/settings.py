#!/usr/bin/python
try:
    from local_settings import *
except ImportError as e:
    from settings_base import *
