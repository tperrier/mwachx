import json,code

def make_original_json():
    
    JSON_DATA_FILE = 'last_backup.json'

    json_data = json.load(open(JSON_DATA_FILE))
    data = {}
    for d in json_data:
        model = d['model'].split('.')[1]
        pk = d['pk']
        fields = d['fields']
        fields['pk'] = pk
        if model == 'client':
            fields.update({
                'messages':[],
                'visits':[],
                'notes':[],
                'delivery':[],
            })
        #save fields to data array
        try:
            data[model][pk] = fields
        except KeyError as e:
            data[model] = {pk:fields}
            
    for pk,fields in data['interaction'].iteritems():
        if pk in data['message']:
            data['message'][pk].update(fields)
            
    for pk,fields in data['message'].iteritems():
        data['client'][fields['client_id']]['messages'].append(fields)
        
    for pk,fields in data['visit'].iteritems():
        data['client'][fields['client_id']]['visits'].append(fields)

    for pk,fields in data['note'].iteritems():
        data['client'][fields['client_id']]['notes'].append(fields)

    for pk,fields in data['pregnancyevent'].iteritems():
        data['client'][fields['client']]['delivery'].append(fields)

    json.dump(data['client'],open('tmp.json','w'),indent=2)
    
def make_small_json():
    
    ids = [88,170,96,4,69,132,68,184,12,261,16,155,25,49,202,30,140,83,143,75]
    original = json.load(open('db.json'))
    small = {i:original[str(i)] for i in ids}
    json.dump(small,open('small.json','w'),indent=2)

make_small_json()
