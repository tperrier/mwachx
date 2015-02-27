import datetime

#Django Imports
from django import forms
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit
from parsley.decorators import parsleyfy


#Local App Imports
import contacts.models as cont
import utils.forms as util
from utils import today

def tmp(t):
    print 'temp'
    return t

@parsleyfy
class ContactAdd(forms.ModelForm):
    
    phone_number = forms.CharField(label='Phone Number', 
        widget=forms.TextInput(attrs={'required':'True','placeholder':'07xxxxxxx','pattern': '^07[0-9]{8}'}))
    
    def __init__(self, *args, **kwargs):
        super(ContactAdd, self).__init__(*args, **kwargs)
        
        #Moved this here so that current date can be calculated for each new form
        
        birth_BO = [{
                'from': (today() - datetime.timedelta(days=14*365)).strftime("%Y-%m-%d"),
                'to': (datetime.datetime(2100,1,1)).strftime("%Y-%m-%d"),
            }]
        due_date_BO = [{
                'from': (datetime.datetime(1970,1,1)).strftime("%Y-%m-%d"), 
                'to': (today() + datetime.timedelta(weeks=4)).strftime("%Y-%m-%d"), # between 4 ....
            }, {
                'from': (today() + datetime.timedelta(weeks=36)).strftime("%Y-%m-%d"), # ...and 36 weeks in the future
                'to': (datetime.datetime(2100,1,1)).strftime("%Y-%m-%d"),
            }]
        art_BO = [{
            'from': today().strftime("%Y-%m-%d"),
            'to': (datetime.datetime(2100,1,1)).strftime("%Y-%m-%d"),
        }]
        self.fields['due_date'].widget = util.FuelDatePicker('due_date', allow_past=True, blackout=due_date_BO, attrs={'required':'True'}) # TODO: Remove the allow_past after testing
        self.fields['birthdate'].widget = util.FuelDatePicker('birthdate', allow_past=True, blackout=birth_BO, attrs={'required':'True'})
        self.fields['art_initiation'].widget = util.FuelDatePicker('art_initiation', allow_past=True, blackout=art_BO)
        
        
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-sm-6'
        self.helper.field_class = 'col-sm-6'
        self.helper.layout = Layout(
            Fieldset(
                'Study Information',
                'study_id',
                'anc_num',
                'study_group',
                'send_day',
                'send_time',
            ), Fieldset (
                'Client Information',
                'nickname',
                'phone_number',
                'birthdate',
                'relationship_status',
                'partner_name',
                'previous_pregnancies',
                'phone_shared',
                'language',
            ), Fieldset (
                'Medical Information',
                'condition',
                'art_initiation',
                'hiv_disclosed',
                'due_date',
            ),
            ButtonHolder(
                Submit('submit', 'Enroll Participant')
            )
        )

    class Meta:
        model = cont.Contact
        exclude = ['status','child_hiv_status','facility']
        
        widgets = {
            # validation
            'study_id': forms.NumberInput(attrs={'min':'100','max':'9999','required':'True'}), # TODO: Update this to be dependent on facility of logged in user
            'anc_num': forms.NumberInput(attrs={'min':'1','max':'5000','required':'True'}), # TODO: Update this to be dependent on facility of logged in user
            'previous_pregnancies': forms.NumberInput(attrs={'min':'0','max':'15'}),
            'study_group': forms.Select(attrs={'required':'True'}),
            'nickname': forms.TextInput(attrs={'required':'True'}),
        }

class ContactModify(forms.ModelForm):
    
    class Meta:
        model = cont.Contact
        fields = ['status','send_day','send_time','art_initiation',
                'hiv_disclosed']

    def __init__(self, *args, **kwargs):
        super(ContactModify, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-7'

        art_BO = [{
            'from': today().strftime("%Y-%m-%d"),
            'to': (datetime.datetime(2100,1,1)).strftime("%Y-%m-%d"),
        }]
        self.fields['art_initiation'].widget = util.FuelDatePicker('art_initiation', allow_past=True, blackout=art_BO)

