
def dispatch(namespace,action,dry_run=True):

    try:
        getattr(namespace,action)(dry_run)
    except AttributeError as e:
        print "Action: {} NOT FOUND".format(action)
