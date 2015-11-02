import json, datetime
from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html

import utils

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
		return formate_html('<div class="datepicker" id="{}" data-allow-past-dates="{}" data-blackout=\'{}\'></div>',
			self.myid,self.allow_past,self.blackout)

class AngularPopupDatePicker(forms.DateInput):

	def __init__(self,attrs=None,max=None,min=None):
		if attrs is None:
			attrs = {}
		if max is not None:
			attrs['max-date'] = convert_date(max)
		if min is not None:
			attrs['min-date'] = convert_date(min)

		attrs['datepicker-popup'] = True
		attrs['is-open'] = 'status.{name}'
		attrs['placeholder'] = 'yyyy-MM-dd'
		super(AngularPopupDatePicker,self).__init__(attrs)

	def render(self,name,value,attrs=None):
		input_str = super(AngularPopupDatePicker,self).render(name,value,attrs)
		input_str = format_html(input_str,name=name)
		tmpl_str = '<p class="input-group">{input_str}<span class="input-group-btn">'
		tmpl_str += '<button type="button" class="btn btn-default" ng-click="status.{name} = !status.{name}">'
		tmpl_str += '<i class="glyphicon glyphicon-calendar"></i></button></span>'
		return format_html(tmpl_str,input_str=input_str,name=name)

def convert_date(date_in):
	date = utils.today()
	if hasattr(date_in,'strftime'): # Date object
		date = date_in
	elif hasattr(date_in,'real'): # number object assume delta days
		date =  utils.today() + datetime.timedelta(days=date_in)

	return "'{}'".format(date.strftime('%Y-%m-%d'))
