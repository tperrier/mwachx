#Django Imports
from django.forms import ModelForm,ModelChoiceField

#Local App Imports
import contacts.models as cont

class SpecialModelChoiceField(ModelChoiceField):

    def label_from_instance(self,obj):
        try:
            return obj.choice_label()
        except AttributeError as e:
            return unicode(obj)

class ParticipantSendForm(ModelForm):

    def __init__(self,*args,**kwargs):
        super(ParticipantSendForm,self).__init__(*args,**kwargs)
        self.fields['contact'] = SpecialModelChoiceField(queryset=cont.Contact.objects.filter(study_group='two-way'))

    class Meta:
        model = cont.Message
        fields = ['text','contact']

class SystemSendForm(ModelForm):

    def __init__(self,*args,**kwargs):
        super(SystemSendForm,self).__init__(*args,**kwargs)
        self.fields['contact'] = SpecialModelChoiceField(queryset=cont.Contact.objects.all())

    class Meta:
        model = cont.Message
        fields = ['text','contact']
