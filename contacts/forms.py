#Django Imports
from django.forms import ModelForm

#Local App Imports
import contacts.models as cont

class ContactAdd(ModelForm):
    
    class Meta:
        model = cont.Contact
        fields = '__all__'
