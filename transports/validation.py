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
def validator_action(contact):
    print 'STOP messaging for {}'.format(contact)
    contact.set_status('stopped','Participant sent stop keyword')

############
validation_validator = Validator('validation')
validators.append(validation_validator)
############

@validation_validator.set('check')
def validator_action(contact,message):
    if not contact.is_validated:
        return contact.validation_key == message.strip()
    return False

@validation_validator.set('action')
def validator_action(contact):
    print 'VALIDATION ACTION for {}'.format(contact)
    contact.is_validated = True
    contact.save()
