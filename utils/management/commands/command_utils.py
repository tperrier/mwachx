import datetime

import contacts.models as cont

def set_edd_calls(email_body):
    ''' Set 14 day post edd call if still pregnant on edd
    To be run every night at 1am'''

    email_body.append( "***** Set EDD Calls *****\n" )

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    edd_today = cont.Contact.objects.filter(due_date=yesterday,status='pregnant',delivery_date__isnull=True)

    email_body.append( "Found {} post edd participants on {}".format(len(edd_today),yesterday) )

    for post in edd_today:
        post.schedule_edd_call()
        email_body.append( "\t{!r}".format(post) )
