""" Helper Functions for openpyxl reports """
import openpyxl as xl

def xl_add_header_row(ws,labels,widths=None,freeze='A2'):
    """ Given a blank workbook adds labels as a header with an auto filter """
    ws.append(labels)
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(labels)) )
    ws.freeze_panes = freeze

    if isinstance(widths, dict):
        ws.freeze_panes = widths.pop('freeze',freeze)
        for col_letter, width in widths.items():
            ws.column_dimensions[col_letter].width = width


def make_column(obj, column):
    if isinstance(column, basestring):
        value = reduce(getattr, column.split('.'), obj)
        if hasattr(value, '__call__'):
            return value()
        return value
    # Else assume column is a function that takes the object
    return column(obj)

bold_font = xl.styles.Font(italic=True,bold=True)

def xl_style_current_row(ws,font=bold_font):
    for cell in ws["{0}:{0}".format(ws._current_row)]:
        cell.font = font
