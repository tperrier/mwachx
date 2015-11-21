import sms_utils as sms

msgs = ['Hello. World','Hello.  World','Hello?     World    ']

for msg in msgs:
    print '{}|{}'.format(msg,sms.clean_msg(msg))
