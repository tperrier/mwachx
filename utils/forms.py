import json
from django import forms
from django.utils.safestring import mark_safe

class Html5DateInput(forms.DateInput):
		input_type = 'date'


class FuelDatePicker(forms.Widget):
	def __init__(self, myid, attrs=None, allow_past=False, blackout=None):
		self.myid = myid
		self.allow_past = str(allow_past).lower()
		self.blackout = "restricted: %s" % json.dumps(blackout)
		if attrs is None:
			attrs = {'readonly': ''}
		super(FuelDatePicker, self).__init__()

	def render(self, name, value, attrs=None):
		return mark_safe(
						"""<div class="datepicker" id="%s">
	<div class="input-group">
		<input class="form-control" id="myDatepickerInput" type="text"/>
		<div class="input-group-btn">
			<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
				<span class="fa fa-calendar"></span>
				<span class="sr-only">Toggle Calendar</span>
			</button>
			<div class="dropdown-menu dropdown-menu-right datepicker-calendar-wrapper" role="menu">
				<div class="datepicker-calendar">
					<div class="datepicker-calendar-header">
						<button type="button" class="prev"><span class="fa fa-chevron-left"></span><span class="sr-only">Previous Month</span></button>
						<button type="button" class="next"><span class="fa fa-chevron-right"></span><span class="sr-only">Next Month</span></button>
						<button type="button" class="title">
								<span class="month">
									<span data-month="0">January</span>
									<span data-month="1">February</span>
									<span data-month="2">March</span>
									<span data-month="3">April</span>
									<span data-month="4">May</span>
									<span data-month="5">June</span>
									<span data-month="6">July</span>
									<span data-month="7">August</span>
									<span data-month="8">September</span>
									<span data-month="9">October</span>
									<span data-month="10">November</span>
									<span data-month="11">December</span>
								</span> <span class="year"></span>
						</button>
					</div>
					<table class="datepicker-calendar-days">
						<thead>
						<tr>
							<th>Su</th>
							<th>Mo</th>
							<th>Tu</th>
							<th>We</th>
							<th>Th</th>
							<th>Fr</th>
							<th>Sa</th>
						</tr>
						</thead>
						<tbody></tbody>
					</table>
					<div class="datepicker-calendar-footer">
						<button type="button" class="datepicker-today">Today</button>
					</div>
				</div>
				<div class="datepicker-wheels" aria-hidden="true">
					<div class="datepicker-wheels-month">
						<h2 class="header">Month</h2>
						<ul>
							<li data-month="0"><button type="button">Jan</button></li>
							<li data-month="1"><button type="button">Feb</button></li>
							<li data-month="2"><button type="button">Mar</button></li>
							<li data-month="3"><button type="button">Apr</button></li>
							<li data-month="4"><button type="button">May</button></li>
							<li data-month="5"><button type="button">Jun</button></li>
							<li data-month="6"><button type="button">Jul</button></li>
							<li data-month="7"><button type="button">Aug</button></li>
							<li data-month="8"><button type="button">Sep</button></li>
							<li data-month="9"><button type="button">Oct</button></li>
							<li data-month="10"><button type="button">Nov</button></li>
							<li data-month="11"><button type="button">Dec</button></li>
						</ul>
					</div>
					<div class="datepicker-wheels-year">
						<h2 class="header">Year</h2>
						<ul></ul>
					</div>
					<div class="datepicker-wheels-footer clearfix">
						<button type="button" class="btn datepicker-wheels-back"><span class="fa fa-arrow-left"></span><span class="sr-only">Return to Calendar</span></button>
						<button type="button" class="btn datepicker-wheels-select">Select <span class="sr-only">Month and Year</span></button>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
<script type="text/javascript">
$(function(){
		$('#%s').datepicker({
			formatDate: function(d){
				return pad(d.getDate(),2) + "-" + pad(d.getMonth()+1,2) + "-" + d.getFullYear();
		},
		allowPastDates: %s,
		%s
	});
});
</script>
""" % (self.myid, self.myid, self.allow_past, self.blackout)
				)

