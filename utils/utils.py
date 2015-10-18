import datetime
from constance import config
from django.conf import settings

def today():
    if not getattr(settings,'FAKE_DATE',True):
        return datetime.date.today()
    elif isinstance(config.CURRENT_DATE,datetime.date):
        return config.CURRENT_DATE
    return datetime.date(*[int(i) for i in config.CURRENT_DATE.split('-')])

def parse_date(datestr):
 	return datetime.datetime.strptime(datestr,'%d-%m-%Y').date()

def angular_datepicker(datestr):
    if hasattr(datestr,'isoformat'):
        return datestr #datestr is a date
    # datestr from angular datepicker is: 2015-10-18T05:54:53.529Z
    return datetime.datetime.strptime(datestr[:10],'%Y-%m-%d').date()

def null_boolean_display(attr):
    if attr is None:
        return 'Unkown'
    elif attr is True:
        return 'Yes'
    return 'No'
