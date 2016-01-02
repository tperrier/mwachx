#!/usr/bin/python
from settings_base import *

MIDDLEWARE_CLASSES += ( 'qinspect.middleware.QueryInspectMiddleware', )

########################################
# QInspect Settings
########################################
QUERY_INSPECT_ENABLED = True
QUERY_INSPECT_LOG_QUERIES = True
# QUERY_INSPECT_LOG_TRACEBACKS = True

# Add loggers
LOGGING['loggers']['qinspect'] = {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }

LOGGING['loggers']['django.db.backends'] = {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
