import datetime
from constance import config
from django.conf import settings
from django.utils import dateparse , timezone
import django.db.models as db

def today(today=None):
    if today is not None:
        return dateparse.parse_date(today) if isinstance(today,basestring) else today
    elif not getattr(settings,'FAKE_DATE',True):
        return datetime.date.today()
    elif isinstance(config.CURRENT_DATE,datetime.date):
        return config.CURRENT_DATE
    return datetime.date(*[int(i) for i in config.CURRENT_DATE.split('-')])

def parse_date(datestr):
 	return datetime.datetime.strptime(datestr,'%d-%m-%Y').date()

def make_date(date,month=0,day=0):
    try:
        new_date = datetime.datetime.combine(date,datetime.time())
    except TypeError as e:
        new_date = datetime.datetime(date,month,day)
    return timezone.make_aware(new_date)

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


def days_as_str(days):
    ''' Return a short string version of days '''
    if -7 <= days <= 7:
        return '{:d}d'.format(days)
    return '{:d}w'.format(int(round(days/7.0)))

class SQLiteDate(db.Func):
    function = 'JULIANDAY'

def sqlite_date_diff(start_date,end_date,days=False):
    ''' return a DjanoORM Expression for the number of seconds/days between start_date and end_data '''
    scale = 86400 if days is False else 1
    return db.ExpressionWrapper( (SQLiteDate(end_date) - SQLiteDate(start_date)) * scale , db.IntegerField() )

def sql_count_when(*qargs,**kwargs):
    """ qargs : list of models.Q objects
        kwargs : filter_term=value dict
    """
    condition = db.Q(**kwargs)
    for q in qargs:
        condition &= q
    return db.Count( db.Case(
        db.When(condition,then=1),output_field=db.IntegerField()
    ))
