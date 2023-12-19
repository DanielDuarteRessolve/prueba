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

def map_moments(moments, categories_found):
    result = []
    elementos_filtrados = []
    for moment in moments:
        elem = {}
        elem['order'] = moment['order']
        elem['moment'] = normalize(moment['moment'])
        elementos_filtrados = [
            e
            for e in categories_found
            if f"{e['category']}-{e['subcategory']}" in moment['categories']
        ]

        categories_found = list(filter(lambda x: x not in elementos_filtrados, categories_found))
        elem['categories_found'] = [f"{i['category']}-{i['subcategory']}" for i in elementos_filtrados]
        elem['categories_found'] = [i for i in elementos_filtrados]
        elem['categories_found_id'] = [i["id"] for i in elementos_filtrados]
        elem['categories_found_id'].sort()

        elem['transcript_found'] = ""
            
        if moment['mode'] == 'ALL':
            elem['mode'] = 'ALL'
            elem["if_found"] = ""
        else:
            elem['mode']='ONE'
            elem["if_found"] = ""
            
        result.append(elem)
    return result

def check_categories(moment_result, categories_found):
    value_mode=3

    for current_moment in moment_result:
        current_moment_categories = current_moment["categories_found"]
        valid_ids = []
        filtered = []
        if len(current_moment["categories_found_id"]) >= 2:
            for id in current_moment["categories_found_id"]:
                foward = categories_found[id:id+value_mode]
                backward = categories_found[id-(value_mode+1):id-1]

                
                for category in current_moment_categories:
                    if (category["id"] in [i["id"] for i in foward] or category["id"] in [i["id"] for i in backward]):
                        # if category["id"]-current_moment_categories[index-1]["id"]<=value_mode:
                        filtered.append(category)
                        valid_ids.append(category["id"])
        else:
            filtered = current_moment_categories
            valid_ids = [i["id"] for i in filtered]
        valid_ids.sort()
        current_moment["categories_found"] = filtered
        current_moment["categories_found_id"] = valid_ids

    return moment_result

def check_moments(moment_result, moments, categories_found):
    value_mode=3
    for i, current_moment in enumerate(moment_result):
 
    # categorias de los momentos del archivo momentos original
        current_result_moment_order = current_moment['order']
        current_original_moments = next((element for element in moments if element["order"] == current_result_moment_order), None)
        original_previous_moment = moments[i - 1] if moments[i]['order'] != 1 else None
        original_next_moment = moments[i + 1] if i < len(moments) - 1 else None
        
        if original_previous_moment != None or original_next_moment != None:
            original_previous_moment = moments[i]

        if len(current_moment["categories_found_id"]) >= 2:
            for current_id in current_moment["categories_found_id"]:
                foward = categories_found[current_id:current_id+value_mode]
                backward = categories_found[current_id-(value_mode+1):current_id-1]
                is_back = False
                is_foward = False
                print("curren_category_id: ", current_id, "\n")
                print("fowared:\n ", foward)
                print("original_next_moment: ", original_next_moment)
                print("\nbackward:\n ", backward)
                print("original_previous_moment: ", original_previous_moment)
                
                for category in backward:
                    _category = f"{category['category']}-{category['subcategory']}" 
                    if (_category in current_moment["categories_found"] or _category in original_previous_moment["categories"]):
                        is_back = True
                        break
                for category in foward:
                    _category = f"{category['category']}-{category['subcategory']}" 
                    if (_category in current_moment["categories_found"] or _category in original_next_moment["categories"]):
                        is_foward = True
                        break
                if not is_back and not is_foward:
                    current_moment["categories_found_id"].remove(current_id)
                    # current_moment["categories_found"].remove(current_id)

        else:
            continue

        return moment_result
            # print(f"MOMENTO RESULTADO ACTUAL {current_original_moments}")
            # print(f"las categorias colindantes en el orginal por izq:{original_previous_moment['categories']}")
            # print(f"las categorias colindantes en el orginal por der:{original_next_moment['categories']}","\n" + "=" * 30 + "\n")
            # verificacion de orden por categorias comparando el resultado con el orden de moments originallt:


result = map_moments(moments, categories_found)
with open('resources/result_map.json', 'w') as json_file:
    json.dump(result, json_file, indent=2)
result = check_categories(result, categories_found)
with open('resources/result_cat.json', 'w') as json_file:
    json.dump(result, json_file, indent=2)
result = check_moments(result, moments, categories_found)
with open('resources/result_moments.json', 'w') as json_file:
    json.dump(result, json_file, indent=2)
 
# marks = [65, 71, 68, 74, 61]

# # convert list to iterator
# iterator_marks = iter(marks)

# # the next element is the first element
# marks_1 = next(iterator_marks)
# print(marks_1)


# print(next(iterator_marks))
# print(next(iterator_marks))
# print(next(iterator_marks))
# print(next(iterator_marks))
# print(next(iterator_marks))

# # Output: 65
# #         71
 
[1,6,7]