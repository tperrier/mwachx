import collections

from django.db import models

import contacts.models as cont

class TopicValue(object):

    def __init__(self):
        self.total = 0
        self.related = 0

    def add_group(self,group):
        self.total += group['count']
        if group['is_related'] is True:
            self.related = group['count']

    @classmethod
    def from_group(cls,group):
        self = cls()
        self.add_group(group)
        return self

def _get_topics():
    incomming = cont.Message.objects.filter(is_outgoing=False,contact__study_group='two-way')
    groups = incomming.order_by().values('topic','is_related').annotate(count=models.Count('id'))
    topics = {}
    for g in groups:
        if g['topic'] in topics:
            topics[g['topic']].add_group(g)
        else:
            topics[g['topic']] = TopicValue.from_group(g)

    return topics


def print_report(parser):
    parser.print_header('Incoming Message Topic (count,precent,related)')

    topics = _get_topics()
    total = sum(t.total for t in topics.values())

    for key , value in topics.items():
        print "{:<20s}{:5d}{: 10.2f}{: 10.2f}".format(key , value.total, value.total*100.0/total, value.related*100/value.total)
    print "{:<20s}{:4d}".format('Total',total)

def csv_report(parser,file_name=None):
    if file_name is None:
        file_name = report_common.defautl_file_name('topics')

    topics = _get_topics()
    total = sum(topics)
