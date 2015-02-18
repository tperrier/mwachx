import datetime
from constance import config
from django.conf import settings

def today():
    if not getattr(settings,'FAKE_DATE',True):
        return datetime.date.today()
    elif isinstance(config.CURRENT_DATE,datetime.date):
        return config.CURRENT_DATE
    return datetime.date(*[int(i) for i in config.CURRENT_DATE.split('-')])
