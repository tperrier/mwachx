class Validator(object):

    def __init__(self,name,check=None,action=None):
        self.name = '{0}_validator'.format(name)
        self.check = check
        self.action = action

    def __call__(self,contact,message):
        return self.check(contact,message)

    def set(self,action):
        if not (action == 'check' or action == 'action'):
            raise TypeError('Invalid action name. Must be "check" or "action".')
        def wrapper(func):
            setattr(self,action,func)
            return func
        return wrapper

class KeywordValidator(Validator):

    def __init__(self,name,action=None):
        def keyword_check(contact,message):
            return name.strip().lower() == message.strip().lower()
        super(KeywordValidator,self).__init__(name,keyword_check,action)
