#Django Imports
from django.conf import settings

#Python Imports
import requests, os, code

#Local Imports
from at_utils import AfricasTalkingException

#Import Afica's Talking Settings
AFRICAS_TALKING_SETTINGS = getattr(settings,'AFRICAS_TALKING',{})

API_KEY = AFRICAS_TALKING_SETTINGS.get('API_KEY',None)

USERNAME = AFRICAS_TALKING_SETTINGS.get('USERNAME',None)

SHORTCODE = AFRICAS_TALKING_SETTINGS.get('SHORTCODE',None)

AFRICAS_TALKING_SEND = AFRICAS_TALKING_SETTINGS.get('SEND',False)

AFRICAS_TALKING_API_BASE = 'http://api.africastalking.com/version1'

HEADERS = {'Accept': 'application/json','apikey':API_KEY}

PARAMS = {'username':USERNAME,'bulkSMSMode':1}
if SHORTCODE:
    PARAMS['from'] = SHORTCODE

def send_raw(to,message):
    if not AFRICAS_TALKING_SEND:
        raise AfricasTalkingException("Africas Talking called when send not set to True")
    if API_KEY is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set API_KEY')
    if USERNAME is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set a USERNAME')

    params = {'to':to,'message':message}
    params.update(PARAMS)

    send_url = os.path.join(AFRICAS_TALKING_API_BASE,'messaging')
    post = requests.post(send_url,data=params,headers=HEADERS)
    #Raise requests.exceptions.HTTPError if 4XX or 5XX
    post.raise_for_status()

    return post.json()

def send(to,message):


    data = send_raw(to,message)
    '''
    Example of JSON Response
    {u'SMSMessageData':
        {u'Message': u'Sent to 1/1 Total Cost: USD 0.0109',
        u'Recipients': [{
            u'status': u'Success', #u'status': u'Invalid Phone Number',
            u'cost': u'KES 1.0000',
            u'number': u'+254708054321',
            u'messageId': u'ATXid_b50fada5b1af078f2277cacb58ef2447'
            }]
        }
    }
    '''
    # Return tuple (messageId, messageSuccess, extra_data)
    recipients = data['SMSMessageData']['Recipients']
    if len(recipients) == 1:
        msg_id = recipients[0]['messageId']
        msg_success = recipients[0]['status'] == 'Success'
        return msg_id, msg_success, {'status':recipients[0]['status']}

def balance():

    if API_KEY is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set API_KEY')
    if USERNAME is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set a USERNAME')

    params = {'username':USERNAME}

    send_url = os.path.join(AFRICAS_TALKING_API_BASE,'user')
    post = requests.get(send_url,params=params,headers=HEADERS)
    #Raise requests.exceptions.HTTPError if 4XX or 5XX
    post.raise_for_status()

    data = post.json()

    return data['UserData']['balance']

def fetch(last_received_id=0):

    if API_KEY is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set API_KEY')
    if USERNAME is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set a USERNAME')

    params = {'username':USERNAME,'lastReceivedId':last_received_id}

    send_url = os.path.join(AFRICAS_TALKING_API_BASE,'messaging')
    post = requests.get(send_url,params=params,headers=HEADERS)

    return post
