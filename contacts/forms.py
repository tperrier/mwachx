# Django Imports
from django import forms
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit
from crispy_forms.bootstrap import FormActions

# Local App Imports
import contacts.models as cont
import utils.forms as util


def contact_add_form_factory(*args, **kwargs):
    if hasattr(settings, 'APP_FLAVOR'):
        if settings.APP_FLAVOR.lower() == 'neo':
            return ContactAddMwachNeo(*args, **kwargs)
        elif settings.APP_FLAVOR.lower() == 'priya':
            return ContactAddMwachPriya(*args, **kwargs)
        else:
            return ContactAddMwachX(*args, **kwargs)
    else:
        return ContactAddMwachPriya(*args, **kwargs)


def contact_update_form_factory(*args, **kwargs):
    if hasattr(settings, 'APP_FLAVOR'):
        if settings.APP_FLAVOR.lower() == 'neo':
            return ContactUpdateMwachNeo(args, kwargs)
        elif settings.APP_FLAVOR.lower() == 'priya':
            return ContactUpdateMwachPriya(*args, **kwargs)
        else:
            return ContactUpdateMwachX(*args, **kwargs)
    else:
        return ContactUpdateMwachPriya(*args, **kwargs)


class ContactAddGeneric(forms.ModelForm):
    # Do not implement Meta in this class, subclasses override it completely

    phone_number = forms.CharField(label='Phone Number',
                                   widget=forms.TextInput(attrs={'required': 'True', 'placeholder': '07xxxxxxx',
                                                                 'pattern': '^07[0-9]{8}'}))

    # clinic_visit = forms.DateField(label='Next Clinic Visit')

    def __init__(self, *args, **kwargs):
        super(ContactAddGeneric, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-sm-6'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_tag = False


class ContactUpdateGeneric(forms.ModelForm):
    # Do not implement Meta in this class, subclasses override it completely

    def __init__(self, *args, **kwargs):
        super(ContactUpdateGeneric, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-7'


class ContactAddMwachPriya(ContactAddGeneric):

    clinic_visit = forms.DateField(label='Next Clinic Visit', required=False)

    def clean_phone_number(self):
        """ Add custom validation for unique phone number """
        phone_number = '+254%s' % self.cleaned_data['phone_number'][1:]
        connection = cont.Connection.objects.get_or_none(identity=phone_number)
        if connection is not None:
            raise forms.ValidationError("Phone number provided already exists", code="unique")
        return self.cleaned_data['phone_number']

    def __init__(self, *args, **kwargs):
        super(ContactAddMwachPriya, self).__init__(*args, **kwargs)

        self.fields['due_date'].widget = util.AngularPopupDatePicker(min=3)
        self.fields['birthdate'].widget = util.AngularPopupDatePicker(
            {'required': True, 'datepicker-position-right': True}, max=-5110  # 14 years or older
        )

        self.fields['clinic_visit'].widget = util.AngularPopupDatePicker( min=7)
        self.fields['prep_initiation'].widget = util.AngularPopupDatePicker( {'required':True}, max=1)

        self.helper.layout = Layout(
            Fieldset(
                'Study Information',
                Div(
                    Div('study_id', css_class="col-md-4"),
                    Div('anc_num', css_class="col-md-4"),
                    Div('send_time', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('phone_number', css_class="col-md-4"),
                    Div('phone_shared', css_class="col-md-4"),
                    Div('send_day', css_class="col-md-4"),
                    css_class="row",
                ),
            ),

            Fieldset(
                'Client Information',
                Div(
                    Div('nickname', css_class="col-md-4"),
                    Div('language', css_class="col-md-4"),
                    Div('condition', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('relationship_status', css_class="col-md-4"),
                    Div('partner_name', css_class="col-md-4"),
                    Div('previous_pregnancies', css_class="col-md-4"),
                    css_class="row"
                ),
            ),


            Fieldset(
                'Important Dates',
                Div(
                    Div('birthdate', css_class="col-md-6"),
                    Div('due_date', css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div('clinic_visit', css_class="col-md-6"),
                    Div('prep_initiation', css_class="col-md-6"),
                    css_class="row"
                )
            ),

            FormActions(
                Submit('submit', 'Enroll Participant', ng_disabled='participantNewForm.$invalid',
                       style='margin-bottom:20px'),
                css_class="row"
            )
        )

        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:
            field.field.widget.attrs.update({
                'ng-model': 'participant.{0}'.format(field.name),
            })

    class Meta:
        # todo: can this be changed to a swappable version?
        model = cont.Contact
        exclude = ['status', 'facility']

        widgets = {
            # validation
            'study_id': forms.TextInput(attrs={'ng-pattern': '/^\d{11}$/', 'required': True}),
            'anc_num': forms.TextInput(attrs={'ng-pattern': '/^\d{4}|(\d{2,}\/)+\d{2,}$/'}),
            'previous_pregnancies': forms.NumberInput(attrs={'min': '0', 'max': '15'}),
            'send_time': forms.Select(attrs={'required': True}),
            'condition': forms.Select(attrs={'required': True}),
            'nickname': forms.TextInput(attrs={'required': True}),
            'language': forms.Select(attrs={'required': True}),
            'phone_shared': forms.NullBooleanSelect(attrs={'required': True}),
        }


class ContactUpdateMwachPriya(ContactUpdateGeneric):
    class Meta:
        # todo: can this be changed to a swappable version?
        model = cont.Contact
        fields = ['send_day', 'send_time', 'due_date', 'prep_initiation', 'condition']

    def __init__(self, *args, **kwargs):
        super(ContactUpdateMwachPriya, self).__init__(*args, **kwargs)

        self.fields['due_date'].widget = util.AngularPopupDatePicker(min=3, max=280)
        self.fields['prep_initiation'].widget = util.AngularPopupDatePicker()

        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:
            field.field.widget.attrs.update({
                'ng-model': 'participant.{0}'.format(field.name),
            })
