import json, re 
from unidecode import unidecode

# Lee el archivo JSON
with open('resources/categories_found.json') as json_file:
    categories_found = json.load(json_file)
with open('resources/moments.json') as json_file:
    moments = json.load(json_file)
with open('resources/transcript.json') as json_file:
    transcript = json.load(json_file)['text']

"""
El modelo fue entrenado con texto normalizado, por lo que es importante asegurarse
que la entrada también lo esté.
"""
def normalize(texto: str) -> str:
    texto_limpio = re.sub(r'\d+\.\d+-\d+\.\d+\|', '', texto)
    texto_limpio = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]', '', texto_limpio)
    texto_limpio = texto_limpio.replace('\n', ' ')
    texto_limpio = ' '.join(texto_limpio.split())
    texto_limpio = unidecode(texto_limpio.lower())
    return texto_limpio


transcript = normalize(transcript)
with open('resources/transcript_normalize.json', 'w') as json_file:
    json.dump({"text": transcript}, json_file, indent=2)

result = []
for index_moment, moment in enumerate(moments):
    elementos_filtrados = []
    elem = {"order": 0, "moment": "", "categories_found": [], "transcript_found": "", "if_found": False, "mode": "ALL", "categories_found_id": []}
    elem['order'] = moment['order']
    elem['moment'] = normalize(moment['moment'])
    
    for index, e in enumerate(categories_found):
        current_category = f"{e['category']}-{e['subcategory']}"
        current_elements = [f"{e['category']}-{e['subcategory']}" for e in elementos_filtrados]
        if current_category in moment['categories']:
            if len(elementos_filtrados) != 0 and current_category in current_elements:
                if e['id'] != elementos_filtrados[-1]['id']+1:
                    continue
            elementos_filtrados.append(e)

    # categories_found = list(filter(lambda x: x not in elementos_filtrados, categories_found))
    elem['categories_found'] = [f"{i['category']}-{i['subcategory']}" for i in elementos_filtrados]
    elem['categories_found_id'] = [i['id'] for i in elementos_filtrados]
    elem['categories_found_id'].sort()

    if len(elem['categories_found_id']) > 0:

        start = elem['categories_found_id'][0]
        end = elem['categories_found_id'][-1]

        index_start = [index for index, value in enumerate(categories_found) if value["id"] == start][0]
        index_end = [index for index, value in enumerate(categories_found) if value["id"] == end][0]
        if moment["order"] == 1:
            index_start = 0

        delete_values = categories_found[index_start:index_end+1]
        categories_found = list(filter(lambda x: x not in delete_values and True, categories_found))

        fragment_start = normalize(elementos_filtrados[0]['fragment_found'])
        fragment_end = normalize(elementos_filtrados[-1]['fragment_found'])
        indexes_start = [match.start() for match in re.finditer(fragment_start, transcript)]
        indexes_end = [match.end() for match in re.finditer(fragment_end, transcript)]
        print(indexes_start, fragment_start, transcript.find(fragment_start))
        print(indexes_end,fragment_end, transcript.find(fragment_end), "\n", "="*10)

        # modificar bien
        fragment_index_start = indexes_start[0]
        fragment_index_end = indexes_end[0]
        if moment["order"] == 1:
            fragment_index_start = 0
        if moment["order"] == len(moments):
            fragment_index_start = len(transcript)-1
        elem['transcript_found'] = transcript[fragment_index_start:fragment_index_end]
        transcript = transcript[fragment_index_end:]
    else:
        elem['transcript_found'] = ""

    if moment['mode'] == 'ALL':
        elem['mode'] = 'ALL'
        elem["if_found"] = all(element in elem['categories_found'] for element in moment['categories'])
    else:
        elem['mode']='ONE'
        elem["if_found"] = any(element in elem['categories_found'] for element in moment['categories'])
        
    result.append(elem)
 
with open('resources/result.json', 'w') as json_file:
    json.dump(result, json_file, indent=2)
 
 
# ignorar las transcripciones que ya se incluyeron en un momento
# el "transcript_found" es la concatenacion de todos los transcripts que corresponden a un momento?