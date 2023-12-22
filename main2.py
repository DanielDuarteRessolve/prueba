import json, re 
from unidecode import unidecode
from operator import itemgetter



class Moments:
    
    def __init__(self) -> None:
        self.categories_found = ""
        self.moments = ""
        self.transcript = ""
        self.main()

    def get_data(self):
        # Lee el archivo JSON
        with open('resources/categories_found.json') as json_file:
            self.categories_found = json.load(json_file)
        with open('resources/moments.json') as json_file:
            self.moments = json.load(json_file)
        with open('resources/transcript.json') as json_file:
            self.transcript = self.normalize(json.load(json_file)['text'])
    
    def write_data(self, data, name_file):
        with open('resources/'+str(name_file), 'w') as json_file:
            json.dump(data, json_file, indent=2)
    
    def normalize(self, texto: str) -> str:
        """
        El modelo fue entrenado con texto normalizado, por lo que es importante asegurarse
        que la entrada también lo esté.
        """
        texto_limpio = re.sub(r'\d+\.\d+-\d+\.\d+\|', '', texto)
        texto_limpio = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]', '', texto_limpio)
        texto_limpio = texto_limpio.replace('\n', ' ')
        texto_limpio = ' '.join(texto_limpio.split())
        texto_limpio = unidecode(texto_limpio.lower())

        return texto_limpio

    def map_moments(self, moments, categories_found):
        result = []
        elementos_filtrados = []
        for moment in moments:
            elem = {}
            elem['order'] = moment['order']
            elem['moment'] = self.normalize(moment['moment'])
            elem['categories'] = moment['categories']
            elem["is_mandatory"] = moment["is_mandatory"]
            elem["mode"] = moment["mode"]
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
            elem['categories_found'] = sorted(elem['categories_found'], key=itemgetter('id')) 

            elem['transcript_found'] = ""
                
            if moment['mode'] == 'ALL':
                elem['mode'] = 'ALL'
                elem["if_found"] = ""
            else:
                elem['mode']='ONE'
                elem["if_found"] = ""
                
            result.append(elem)
        return result

    def check_context(self, moment_result, value_mode_context):

        for current_moment in moment_result:
            current_moment["context_found"] = []
            context = []
            ids = current_moment["categories_found_id"]
            for index, id in enumerate(ids):
                if index>0:
                    prev_id = ids[index-1]
                else:
                    prev_id = id
                
                if id-prev_id<=value_mode_context:
                    context.append(id)
                else:
                    context = []
                    context.append(id)

                current_moment["context_found"].append({"context":context})

            unique_contexts = []
            for item in current_moment["context_found"]:
                if item not in unique_contexts:
                    unique_contexts.append(item)

            for index, context in enumerate(unique_contexts):
                context["id"] = index

            # Actualizar la lista original
            current_moment["context_found"] = unique_contexts 

        return moment_result

    def check_categories(self, moment_result, categories_found):
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

    def check_moments(self, moment_result, moments, categories_found, value_mode_moment):

        for i, current_moment in enumerate(moment_result):
    
        # categorias de los momentos del archivo momentos original
            current_result_moment_order = current_moment['order']
            current_original_moments = next((element for element in moments if element["order"] == current_result_moment_order), None)
            previous_moments = [moment for moment in moment_result if moment["order"] < current_result_moment_order]
            next_moments = [moment for moment in moment_result if moment["order"] > current_result_moment_order]
            
            if len(previous_moments) == 0:
                previous_moments = [current_moment]
            if len(next_moments) == 0:
                next_moments = [current_moment]
            
            previous_moments = sorted(previous_moments, key=itemgetter('order'), reverse=True)
            print(current_moment["moment"] + " order: " + str(current_moment["order"]))
            context_to_delete = []
            for index, context_obj in enumerate(current_moment["context_found"]):
                print("context: ", context_obj["context"])
                context_ids = context_obj["context"]
                context_start = context_ids[0]
                context_end = context_ids[-1]

                foward = categories_found[context_end:context_end+value_mode_moment]
                start=context_start-(value_mode_moment+1)
                end=context_start-1
                if start<0:
                    start=0
                if end<0:
                    end=context_end
                backward = categories_found[start:end]

                foward_categories = [f"{category['category']}-{category['subcategory']}" for category in foward]
                backward_categories = [f"{category['category']}-{category['subcategory']}" for category in backward]

                is_back = False
                is_foward = False
                print("foward_categories: ", foward_categories)
                print("backward_categories: ", backward_categories)
                print("previus_moments: ", previous_moments)
                print("next_moments: ", next_moments)

                # check in backward moments
                print("PREV MOMENTS")
                for prev_moment in previous_moments:
                    print("prev_moment: ", prev_moment["moment"]+"-",prev_moment["order"])
                    prev_moment_categories = prev_moment["categories"]
                    if len(prev_moment["categories_found"]) == 0:
                        print("categories_found vacio")
                        print("no in moment prev: ", prev_moment["moment"])
                        continue
                    for category in backward_categories:
                        print("current category: ", category)
                        if (category in prev_moment_categories):
                            is_back = True
                            print("la categoría:", category, "esta en el momento previo:", prev_moment["moment"]+"-",prev_moment["order"])
                            break
                    if is_back:
                        break
                print("¿LO ENCONTRÓ ATRÁS?: ", is_back)
                
                # check in foward moments
                print("NEXT MOMENTS")
                for next_moment in next_moments:
                    print("next_moment: ", next_moment["moment"]+"-",next_moment["order"])
                    next_moment_categories = next_moment["categories"]
                    if len(next_moment["categories_found"]) == 0:
                        print("categories_found vacio")
                        print("no in moment next: ", next_moment["moment"])

                        if next_moment["order"] == moment_result[-1]["order"]:
                            is_foward = True
                            print("es el ultimo momento")
                            break
                        continue
                    for category in foward_categories:
                        print("current category: ", category)
                        if (category in next_moment_categories):
                            is_foward = True
                            print("la categoría:", category, "esta en el momento posterior:", next_moment["moment"]+"-",next_moment["order"])
                            break
                    if is_foward:
                        break
                    else:
                        if next_moment["is_mandatory"]:
                            break
                print("¿LO ENCONTRÓ ADELANTE?: ", is_foward)

                print("is_back: ", is_back)
                print("is_foward: ", is_foward)
                if (not is_back and not current_moment["order"] == 1) or (not is_foward and not current_moment["order"] == moment_result[-1]["order"]):
                    context_to_delete.append(context_obj["id"])
                    print("false moment")
                else:
                    print("true moment")
            print("context to delete: ", context_to_delete)
            current_moment["context_found_filtered"] = [context for context in current_moment["context_found"] if context["id"] not in context_to_delete]
            
        return moment_result

    def main(self):
        try:
            self.get_data()

            result_map = self.map_moments(self.moments, self.categories_found)
            result_context = self.check_context(result_map, value_mode_context=3)
            result_moments = self.check_moments(result_context, self.moments, self.categories_found, value_mode_moment=3)
            
            self.write_data(result_moments, "result_moments.json")
            self.write_data({"text": self.transcript}, "transcript_normalize.json")
        except Exception as e:
            print(e)

Moments()