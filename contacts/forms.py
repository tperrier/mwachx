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

    def clean_phone_number(self):
        ''' Add custom validation for unique phone number '''
        phone_number = '+254%s'%self.cleaned_data['phone_number'][1:]
        connection = cont.Connection.objects.get_or_none(identity=phone_number)
        if connection is not None:
            raise forms.ValidationError("Phone number provided already exists",code="unique")
        return self.cleaned_data['phone_number']

    clinic_visit = forms.DateField(label='Next Clinic Visit')

    def __init__(self, *args, **kwargs):
        super(ContactAdd, self).__init__(*args, **kwargs)

        self.fields['due_date'].widget = util.AngularPopupDatePicker({'required':True},min=3)
        self.fields['birthdate'].widget = util.AngularPopupDatePicker(
            {'required':True,'datepicker-position-right':True},max=-5110 # 14 years or older
        )
        self.fields['art_initiation'].widget = util.AngularPopupDatePicker(max=0)
        self.fields['clinic_visit'].widget = util.AngularPopupDatePicker({'required':True}, min=7)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-sm-6'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_tag = False

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
                    Div('ccc_num', css_class="col-md-4"),
                    Div('send_day', css_class="col-md-4", ng_if="participant.study_group != 'control'" ),
                    Div('send_time', css_class="col-md-4", ng_if="participant.study_group != 'control'" ),
                    css_class="row",
                ),
            ),

            Fieldset (
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
                    Div('language', css_class="col-md-4"),
                    Div('condition', css_class="col-md-4"),
                    css_class="row"
                ),
            ),

            Fieldset (
                'Disclosure and Consent',
                Div(
                    Div('hiv_disclosed', css_class="col-md-4"),
                    Div('phone_shared', css_class="col-md-4"),
                    Div('hiv_messaging', css_class="col-md-4"),
                    css_class="row"
                )
            ),

            Fieldset (
                'Important Dates',
                Div(
                    Div('art_initiation', css_class="col-md-4"),
                    Div('due_date', css_class="col-md-4"),
                    Div('clinic_visit', css_class="col-md-4"),
                    css_class="row"
                )
            ),
            FormActions(
                Submit('submit', 'Enroll Participant',ng_disabled='participantNewForm.$invalid', style='margin-bottom:20px'),
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
        exclude = ['status','facility']

        widgets = {
            # validation
            'study_id': forms.TextInput(attrs={'ng-pattern':'/^(\d{4}|25\d{6}0)$/','required':True}), # TODO: Update this to be dependent on facility of logged in user
            'anc_num': forms.TextInput(attrs={'ng-pattern':'/^\d{4}|(\d{2,}\/)+\d{2,}$/','required':True}),
            'ccc_num': forms.TextInput(attrs={'required':True}),
            'previous_pregnancies': forms.NumberInput(attrs={'min':'0','max':'15'}),
            'study_group': forms.Select(attrs={'required':True}),
            'send_day': forms.Select(attrs={'required':True}),
            'send_time': forms.Select(attrs={'required':True}),
            'condition': forms.Select(attrs={'required':True}),
            'nickname': forms.TextInput(attrs={'required':True}),
            'language': forms.Select(attrs={'required':True}),
            'hiv_disclosed': forms.NullBooleanSelect(attrs={'required':True}),
            'phone_shared': forms.NullBooleanSelect(attrs={'required':True}),
            'hiv_messaging': forms.Select(attrs={'required':True}),
        }

class ContactUpdate(forms.ModelForm):

    class Meta:
        model = cont.Contact
        fields = ['send_day','send_time','due_date','art_initiation','hiv_messaging', 'hiv_disclosed','second_preg']

    def __init__(self, *args, **kwargs):
        super(ContactUpdate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-7'

        self.fields['art_initiation'].widget = util.AngularPopupDatePicker(max=0)
        self.fields['due_date'].widget = util.AngularPopupDatePicker(min=3,max=280)

        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:

          field.field.widget.attrs.update({
              'ng-model': 'participant.{0}'.format(field.name),
          })
