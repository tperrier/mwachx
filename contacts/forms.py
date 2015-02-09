#Django Imports
from django import forms


#Local App Imports
import contacts.models as cont
import utils.forms as util

class ContactAdd(forms.ModelForm):
    
    phone_number = forms.CharField(max_length=20,label='Phone Number')
    
    class Meta:
        model = cont.Contact
        exclude = ['status','child_hiv_status']
        
        widgets = {
            'due_date': util.FuelDatePicker('due_date'),
            'birthdate': util.FuelDatePicker('birthdate', allow_past=True),
            'art_initiation': util.FuelDatePicker('art_initiation', allow_past=True),
        }

class ContactModify(forms.ModelForm):
    
    class Meta:
        model = cont.Contact
        fields = ['status','family_planning','art_initiation','child_hiv_status',
                'hiv_disclosed','relationship_status','partner_name']
