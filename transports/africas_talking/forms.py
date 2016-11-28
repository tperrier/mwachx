from django import forms

class AfricasTalkingForm(forms.Form):

    def __init__(self,*args,**kwargs):
        super(AfricasTalkingForm,self).__init__(*args,**kwargs)
        self.fields['from'] = forms.CharField()

    to = forms.CharField(label='Receiving ShortCode')
    text = forms.CharField(label='Message')
    date = forms.CharField()
    id = forms.CharField()
    linkId = forms.CharField()
