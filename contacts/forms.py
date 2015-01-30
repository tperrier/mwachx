#Django Imports
from django import forms

#Local App Imports
import contacts.models as cont
import utils.forms as util

class ContactAdd(forms.ModelForm):
    
    phone_number = forms.CharField(max_length=20,label='Phone Number')
    
    class Meta:
        model = cont.Contact
        exclude = ['status']
        
        widgets = {
            'due_date':util.Html5DateInput(),
            'birthdate':util.Html5DateInput(),
        }
