import collections

from django.db import models

import contacts.models as cont


def print_report(parser):
    parser.print_header('Message Counts By Auto Tag')

    system_msgs = cont.Message.objects.filter(is_system=True).exclude(auto='')

    groups = system_msgs.order_by().values('auto').annotate(count=models.Count('id'))

    auto_counts = collections.defaultdict(list)

    for g in groups:
        split = g['auto'].split('.')
        auto_group = (split[0],int(split[-1]))
        auto_counts[auto_group].append(g)

    for auto_group , sub_groups in sorted(auto_counts.items()):
        print '{0[0]}.{0[1]} -- ({1})'.format(auto_group,sum(g['count'] for g in sub_groups))
        for auto in sub_groups:
            print "\t{0[auto]} -- ({0[count]})".format(auto)
