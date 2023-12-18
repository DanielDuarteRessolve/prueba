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

class bidirectional_iterator(object):
    def __init__(self, collection):
        self.collection = collection
        self.index = 0

    def next(self):
        try:
            result = self.collection[self.index]
            self.index += 1
        except IndexError:
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            raise StopIteration
        return self.collection[self.index]

    def __iter__(self):
        return self
    
def check_categories(moment_result, categories_found):
    value_mode=3

    for current_moment in moment_result:
        current_moment_categories = current_moment["categories_found"]
        valid_ids = []
        for id in current_moment["categories_found_id"]:
            foward = categories_found[id:id+value_mode]
            backward = categories_found[id-(value_mode+1):id-1]
            filtered = []
            
            for category in current_moment_categories:
                if (category["id"] in [i["id"] for i in foward] or category["id"] in [i["id"] for i in backward]):
                    filtered.append(category)
                    valid_ids.append(category["id"])

            print(current_moment["moment"], "--", id, "--", categories_found[id-1]["category"], "-", categories_found[id-1]["subcategory"])
            print("current: ", current_moment_categories)
            print("foward: ", foward)
            print("backware: ", backward)
            print(filtered)
        current_moment["categories_found"] = filtered
        current_moment["categories_found_id"] = valid_ids

        # ids = moment['categories_found_id']
        # for i in range(len(ids)):
        #     if i < len(ids)-1:
        #         if ids[i+1]-ids[i]>=value_mode:
        #             ids = ids[:i+1]

        # moment['categories_found_id'] = ids
    return moment_result


result = map_moments(moments, categories_found)
with open('resources/result_map.json', 'w') as json_file:
    json.dump(result, json_file, indent=2)
result = check_categories(result, categories_found)
with open('resources/result_cat.json', 'w') as json_file:
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