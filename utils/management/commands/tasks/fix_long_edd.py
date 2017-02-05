# Python Imports
import datetime
import functools

# Local imports
import contacts.models as cont

def main(dry_run=True):
    """ Set edd to 35 weeks after registration for far future edds """

    future_35wk = datetime.date.today() + datetime.timedelta(weeks=35)
    participants = cont.Contact.objects.filter(due_date__gt=future_35wk)

    print "Count: {} Dry-Run: {}".format(participants.count(),dry_run)
    map( functools.partial(update_participant,dry_run=dry_run) , participants.all() )

def update_participant(participant,dry_run=True):
    new_edd = participant.created.date() + datetime.timedelta(weeks=35)
    print "  {0.study_id} -- {1} -- {0.due_date} -- {2.days} -- {3}".format(
        participant, participant.created.date(), participant.due_date - datetime.date.today(), new_edd
    )
    if dry_run is not True:
        participant.note_set.create(
            comment="Inital EDD out of range. Script changed EDD from {} to {} (35 weeks from enrollment).".format(
                participant.due_date.strftime("%Y-%m-%d"),
                new_edd.strftime("%Y-%m-%d")
            )
        )

        participant.due_date = new_edd
        participant.save()
