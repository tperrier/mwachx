
def send(identity,message):
    ''' Dummy Send Function '''
    print 'Default Send: {0} {1}'.format(identity,message.encode('utf-8'))
    return 'Default Transport', True, {}
