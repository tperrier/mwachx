import collections

from django.db import models

import contacts.models as cont

catagories = ['participant', 'nurse_s', 'nurse_u','nurse_f','system_s','system_u','system_f','none']

def _get_statuses():
    msgs = cont.Message.objects.all().order_by('created')
    statuses = collections.OrderedDict()

    for m in msgs:
        week = m.created.strftime('%Y-%m (%W)')
        if week not in statuses:
            statuses[week] = {cat:0 for cat in catagories}
        if m.external_status == 'Success':
            cat = 'system_s' if m.is_system else 'nurse_s'
        elif m.external_status == 'Sent':
            cat = 'system_u' if m.is_system else 'nurse_u'
        elif m.is_outgoing:
            cat = 'system_f' if m.is_system else 'system_f'
        else: # incoming message
            cat = 'participant' if m.contact is not None else 'none'
        statuses[week][cat] += 1
    return statuses

def print_row(row):
    print '{0[0]:^6}{0[1]:^13}{0[2]:^9}{0[3]:^9}{0[4]:^9}{0[5]:^10}{0[6]:^10}{0[7]:^10}{0[8]:^6}'.format(row)

def print_statuses():
    print_row(['week'] + catagories)
    statuses = _get_statuses()
    for week , counts in statuses.items():
        print_row([week] + [counts[cat] for cat in catagories])
