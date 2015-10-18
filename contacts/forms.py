import datetime

#Django Imports
from django import forms
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit
from crispy_forms.bootstrap import FormActions


#Local App Imports
import contacts.models as cont
import utils.forms as util
from utils import today


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
        self.fields['due_date'].widget = util.AngularPopupDatePicker({'required':True})
        self.fields['birthdate'].widget = util.AngularPopupDatePicker({'required':True,'datepicker-position-right':True})
        self.fields['art_initiation'].widget = util.AngularPopupDatePicker()


        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-sm-6'
        self.helper.field_class = 'col-sm-6'
        self.helper.layout = Layout(
            Fieldset(
                'Study Information',
                Div(
                    Div('study_id', css_class="col-md-4"),
                    Div('anc_num', css_class="col-md-4"),
                    Div('study_group', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('send_day', css_class="col-md-4"),
                    Div('send_time', css_class="col-md-4"),
                    css_class="row",
                    ng_if="participant.study_group != 'control'"
                ),
            ), Fieldset (
                'Client Information',
                Div(
                    Div('nickname', css_class="col-md-4"),
                    Div('phone_number', css_class="col-md-4"),
                    Div('birthdate', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('relationship_status', css_class="col-md-4"),
                    Div('partner_name', css_class="col-md-4"),
                    Div('previous_pregnancies', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('phone_shared', css_class="col-md-4"),
                    Div('language', css_class="col-md-4"),
                    css_class="row"
                ),
            ), Fieldset (
                'Medical Information',
                Div(
                    Div('condition', css_class="col-md-4"),
                    Div('art_initiation', css_class="col-md-4"),
                    Div('hiv_disclosed', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('due_date', css_class="col-md-4"),
                    css_class="row"
                )
            ),
            FormActions(
                Submit('submit', 'Enroll Participant'),
                css_class="row"
            )
        )


        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:

          field.field.widget.attrs.update({
              'ng-model': 'participant.{0}'.format(field.name),
          })

    class Meta:
        model = cont.Contact
        exclude = ['status','child_hiv_status','facility']

        widgets = {
            # validation
            'study_id': forms.TextInput(attrs={'ng-pattern':'/^(\d{4}|25\d{6}0)$/','required':True}), # TODO: Update this to be dependent on facility of logged in user
            'anc_num': forms.TextInput(attrs={'ng-pattern':'/^\d{4}\/\d{2}$/','required':True}), # TODO: Update this to be dependent on facility of logged in user
            'previous_pregnancies': forms.NumberInput(attrs={'min':'0','max':'15'}),
            'study_group': forms.Select(attrs={'required':True}),
            'send_day': forms.Select(attrs={'required':True}),
            'send_time': forms.Select(attrs={'required':True}),
            'condition': forms.Select(attrs={'required':True}),
            'nickname': forms.TextInput(attrs={'required':True}),
            'language': forms.Select(attrs={'required':True})
        }

class ContactUpdate(forms.ModelForm):

    class Meta:
        model = cont.Contact
        fields = ['status','send_day','send_time','art_initiation',
                'hiv_disclosed']

    def __init__(self, *args, **kwargs):
        super(ContactUpdate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-7'

        art_BO = [{
            'from': today().strftime("%Y-%m-%d"),
            'to': (datetime.datetime(2100,1,1)).strftime("%Y-%m-%d"),
        }]
        self.fields['art_initiation'].widget = util.AngularPopupDatePicker()

        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:

          field.field.widget.attrs.update({
              'ng-model': 'participant.{0}'.format(field.name),
          })
