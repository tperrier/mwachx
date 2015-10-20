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
    if datestr is None or hasattr(datestr,'isoformat'):
        return datestr #datestr is a date
    # datestr from angular datepicker is: 2015-10-18T05:54:53.529Z
    return datetime.datetime.strptime(datestr[:10],'%Y-%m-%d').date()

def null_boolean_display(bool_value):
    return {True:'Yes',
            False:'No',
            None:'Unkown'}.get(bool_value)

def null_boolean_form_value(bool_value):
    '''
    Return the value for a NullBooleanSelect wigit based on bool_value
    '''
    return {True:'2',False:'3',None:'1'}.get(bool_value)

def null_boolean_from_form(form_value):
    '''
    Return the boolean value based on a NullBooleanSelect form value
    '''
    return {'1':None,'2':True,'3':False}.get(form_value)
