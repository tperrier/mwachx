import json
from django import forms
from django.utils.safestring import mark_safe

class Html5DateInput(forms.DateInput):
		input_type = 'date'


class FuelDatePicker(forms.Widget):
	def __init__(self, myid, attrs=None, allow_past=False, blackout=None):
		self.myid = myid
		self.allow_past = str(allow_past).lower()
		self.blackout = json.dumps(blackout)
		if attrs is None:
			attrs = {'readonly': ''}
		super(FuelDatePicker, self).__init__()

	def render(self, name, value, attrs=None):
		return mark_safe('<div class="datepicker" id="%s" data-allow-past-dates="%s" data-blackout=\'%s\'></div>'%(self.myid,self.allow_past,self.blackout))


