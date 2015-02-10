import datetime

#Django Imports
from django import forms
from django.conf import settings


#Local App Imports
import contacts.models as cont
import utils.forms as util

class ContactAdd(forms.ModelForm):
    
    phone_number = forms.CharField(label='Phone Number', widget=forms.TextInput(attrs={'required':'True','placeholder':'07xxxxxxx','pattern': '^07[0-9]{8}'}))
    
    class Meta:
        model = cont.Contact
        exclude = ['status','child_hiv_status']


        birth_BO = [{
                'from': (settings.CURRENT_DATE - datetime.timedelta(days=14*365)).strftime("%m/%d/%Y"),
                'to': (datetime.datetime(2100,1,1)).strftime("%m/%d/%Y"),
            }]
        due_date_BO = [{
                'from': (datetime.datetime(1970,1,1)).strftime("%m/%d/%Y"), 
                'to': (settings.CURRENT_DATE + datetime.timedelta(weeks=4)).strftime("%m/%d/%Y"), # between 4 ....
            }, {
                'from': (settings.CURRENT_DATE + datetime.timedelta(weeks=36)).strftime("%m/%d/%Y"), # ...and 36 weeks in the future
                'to': (datetime.datetime(2100,1,1)).strftime("%m/%d/%Y"),
            }]
        art_BO = [{
            'from': (settings.CURRENT_DATE).strftime("%m/%d/%Y"),
            'to': (datetime.datetime(2100,1,1)).strftime("%m/%d/%Y"),
        }]
        
        widgets = {
            'due_date': util.FuelDatePicker('due_date', allow_past=True, blackout=due_date_BO, attrs={'required':'True'}), # TODO: Remove the allow_past after testing
            'birthdate': util.FuelDatePicker('birthdate', allow_past=True, blackout=birth_BO, attrs={'required':'True'}),
            'art_initiation': util.FuelDatePicker('art_initiation', allow_past=True, blackout=art_BO),
            # validation
            'study_id': forms.NumberInput(attrs={'min':'1000','max':'9999','required':'True'}), # TODO: Update this to be dependent on facility of logged in user
            'anc_num': forms.NumberInput(attrs={'min':'1','max':'5000','required':'True'}), # TODO: Update this to be dependent on facility of logged in user
            'study_group': forms.Select(attrs={'required':'True'}),
            'nickname': forms.TextInput(attrs={'required':'True'}),
        }

class ContactModify(forms.ModelForm):
    
    class Meta:
        model = cont.Contact
        fields = ['status','family_planning','art_initiation','child_hiv_status',
                'hiv_disclosed','relationship_status','partner_name']
