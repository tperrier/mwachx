#Django Imports
from django.forms import ModelForm

#Local App Imports
import contacts.models as cont

class MessageSendForm(ModelForm):
    
    class Meta:
        model = cont.Message
        fields = ['text','contact']
