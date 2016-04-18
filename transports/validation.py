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

@stop_validator.set('action')
def validator_action(message):
    print 'STOP messaging for {}'.format(message.contact)
    message.contact.set_status('stopped','Participant sent stop keyword')
    message.text += ' - participant withdrew'
    message.contact.send_automated_message(
        send_base='stop',
        send_offset=0,
        group='one-way',
        hiv_messaging=False
    )
    return False

###############
validation_validator = Validator('validation')
validators.append(validation_validator)

@validation_validator.set('check')
def validator_action(message):
    if re.match('^\d{5}$',message.text) and not message.contact.is_validated:
        message.topic = 'validation'
        message.is_related = True
        message.is_viewed = True
        if message.contact.validation_key == message.text.strip():
            message.text = 'Validation Code Correct: ' + message.text
            return True
        else:
            message.text = 'Validation Code Incorrect: ' + message.text
            return False
    return False

@validation_validator.set('action')
def validator_action(message):
    # print 'VALIDATION ACTION for {}'.format(contact)
    message.contact.is_validated = True
    message.contact.save()

###############
study_group_validator = Validator('study_group')
validators.append(study_group_validator)

@study_group_validator.set('check')
def validator_action(message):
    if message.contact.study_group in ('one-way','control'):
        message.text = "WARNGING: {} {}".format(message.contact.study_group.upper(), message.text)
        message.is_viewed = True
        return True
    return False

@study_group_validator.set('action')
def validator_action(message):
    # Send contact bounce message
    message.contact.send_automated_message(send_base='bounce',send_offset=0,hiv_messaging=False,control=True)
