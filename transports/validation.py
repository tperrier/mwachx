import re
from validators import KeywordValidator, Validator

# Arrary of validator actions
validators = []

########################################
# Define Validators
########################################

#############
stop_validator = KeywordValidator('stop')
validators.append(stop_validator)
############

@stop_validator.set('action')
def validator_action(contact,message):
    print 'STOP messaging for {}'.format(contact)
    contact.set_status('stopped','Participant sent stop keyword')

############
validation_validator = Validator('validation')
validators.append(validation_validator)
############


@validation_validator.set('check')
def validator_action(contact,message):
    if re.match('^\d{5}$',message) and not contact.is_validated:
        if contact.validation_key == message.strip():
            message = 'Validation Code Correct: ' + message
            return True, {'topic':'validation','is_related':True,'is_viewed':True}, message
        else:
            message = 'Validation Code Incorrect: ' + message
            return False, {'topic':'validation','is_related':True,'is_viewed':True}, message
    return False, {}

@validation_validator.set('action')
def validator_action(contact,message):
    print 'VALIDATION ACTION for {}'.format(contact)
    contact.is_validated = True
    contact.save()
