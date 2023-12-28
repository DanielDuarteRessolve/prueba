import json, re 
from unidecode import unidecode
from operator import itemgetter
import math



class Moments:
    
    def __init__(self) -> None:
        self.categories_found = ""
        self.moments = ""
        self.transcript = ""
        self.constante_penalizacion = 0.1
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
            elem["is_found"] = False
            elem["moment_percentage"] = 1
            elem['transcript_found'] = ""

            elementos_filtrados = [
                e
                for e in categories_found
                if f"{e['category']}-{e['subcategory']}" in moment['categories']
            ]

            # categories_found = list(filter(lambda x: x not in elementos_filtrados, categories_found))
            elem['categories_found'] = [f"{i['category']}-{i['subcategory']}" for i in elementos_filtrados]
            elem['categories_found'] = [i for i in elementos_filtrados]
            elem['categories_found_id'] = [i["id"] for i in elementos_filtrados]
            elem['categories_found_id'].sort()
            elem['categories_found'] = sorted(elem['categories_found'], key=itemgetter('id')) 

            if len(elem['categories_found']) == 0:
                elem["is_found"] = False
                elem["moment_percentage"] = 0
                
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
        
        moment_result = self.check_context_percentage(moment_result, value_mode_context)
        return moment_result

    def penalization(self, relevant_percentage, aditional_penalization):
        porcentaje_penalizado = relevant_percentage * math.exp(-self.constante_penalizacion * aditional_penalization)
        relevant_percentage_result = max(0, min(1, porcentaje_penalizado))
        return relevant_percentage_result

    def check_context_percentage(self, moment_result, value_mode_context):
        for current_moment in moment_result:
            print("Momento: ", current_moment["moment"] + " - " + str(current_moment["order"]))
            for context in current_moment["context_found"]:
                print("Contexto: ", context["context"])
                context["relevant_percentage"] = 1
                relevant_percentage_list = []
                values_distance = 0
                for index, id in enumerate(context["context"]):
                    if index<len(context["context"])-1:
                        next_id = context["context"][index+1]
                    else:
                        next_id = id
                    distance = next_id-id
                    if distance > 1:
                        values_distance += distance

                    obj = next((element for element in current_moment["categories_found"] if element["id"] == id), None)
                    relevant_percentage_list.append(obj["relevant_percentage"])

                # Penalización por revelevant_percentage
                print("penalizacion por relevant_percentage")
                print("value before: ", context["relevant_percentage"])
                percentage_mean = sum(relevant_percentage_list)/len(relevant_percentage_list)
                context["relevant_percentage"] -= percentage_mean * self.constante_penalizacion
                print("value after: ", context["relevant_percentage"])
                # Penalización por distancia entre categorías en un contexto
                print("penalizacion por distancia entre categorías en un contexto")
                print("Distancia acumuladas: ", values_distance)
                print("value before: ", context["relevant_percentage"])
                context["relevant_percentage"] = self.penalization(context["relevant_percentage"], values_distance)
                print("value after: ", context["relevant_percentage"])

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
            print("-----" + current_moment["moment"] + " order: " + str(current_moment["order"]))
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
                    distance = int(current_moment["order"]) - int(prev_moment["order"])
                    if len(prev_moment["categories_found"]) == 0:
                        print("categories_found vacio")
                        print("no in moment prev: ", prev_moment["moment"])
                        if prev_moment["order"] == 1:
                            is_back = True
                            print("es el primer momento")
                            break
                        if prev_moment["is_mandatory"]:
                            # Penalización por is_mandatory
                            print("Penalización por is_mandatory")
                            print("value before 212: ", context_obj["relevant_percentage"])
                            
                            context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], value_mode_moment)
                            print("value after: " , context_obj["relevant_percentage"])
                            # Penalización por distancia entre momentos y id decimal
                            print("distnace moments before: ", distance)
                            if distance > 1 and type(prev_moment["order"]) == int:
                                print("Penalización por distancia entre momentos")
                                print("distnace", distance)
                                print("value before: ", context_obj["relevant_percentage"])
                                context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], distance)
                                print("value after: " , context_obj["relevant_percentage"])
                        continue
                    for category in backward_categories:
                        print("current category: ", category)
                        if (category in prev_moment_categories):
                            is_back = True
                            print("la categoría:", category, "esta en el momento previo:", prev_moment["moment"]+"-",prev_moment["order"])
                            break
                    if is_back:
                        break
                    else:
                        if prev_moment["is_mandatory"]:
                            # Penalización por is_mandatory
                            print("Penalización por is_mandatory")
                            print("value before 237: ", context_obj["relevant_percentage"])
                            print("\n ------------****** contex_obj: ", context_obj)
                            context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], value_mode_moment)
                            print("value after: " , context_obj["relevant_percentage"])
                            # Penalización por distancia entre momentos y id decimal
                            if distance > 1 and type(prev_moment["order"]) == int:
                                print("Penalización por distancia entre momentos")
                                print("distnace", distance)
                                print("value before: ", context_obj["relevant_percentage"])
                                context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], distance)
                                print("value after: " , context_obj["relevant_percentage"])
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
                        if next_moment["is_mandatory"]:
                            # Penalización por is_mandatory
                            print("Penalización por is_mandatory")
                            print("value before: ", context_obj["relevant_percentage"])
                            context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], value_mode_moment)
                            print("value after: " , context_obj["relevant_percentage"])
                            # Penalización por distancia entre momentos y id decimal
                            distance = int(next_moment["order"]) - int(current_moment["order"])
                            if distance > 1 and type(next_moment["order"]) == int:
                                print("Penalización por distancia entre momentos")
                                print("distnace", distance)
                                print("value before: ", context_obj["relevant_percentage"])
                                context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], distance)
                                print("value after: " , context_obj["relevant_percentage"])
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
                            # Penalización por is_mandatory
                            print("Penalización por is_mandatory")
                            print("value before: ", context_obj["relevant_percentage"])
                            context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], value_mode_moment)
                            print("value after: " , context_obj["relevant_percentage"])
                            # Penalización por distancia entre momentos y id decimal
                            distance = int(next_moment["order"]) - int(current_moment["order"])
                            if distance > 1 and type(next_moment["order"]) == int:
                                print("Penalización por distancia entre momentos")
                                print("distnace", distance)
                                print("value before: ", context_obj["relevant_percentage"])
                                context_obj["relevant_percentage"] = self.penalization(context_obj["relevant_percentage"], distance)
                                print("value after: " , context_obj["relevant_percentage"])
                            break

                print("¿LO ENCONTRÓ ADELANTE?: ", is_foward)

                print("is_back: ", is_back)
                print("is_foward: ", is_foward)
                if (not is_back and not current_moment["order"] == 1) and (not is_foward and not current_moment["order"] == moment_result[-1]["order"]):
                    context_to_delete.append(context_obj["id"])
                    print("false moment")
                else:
                    print("true moment")
            print("context to delete: ", context_to_delete)
            # current_moment["context_found_filtered"] = [context for context in current_moment["context_found"] if context["id"] not in context_to_delete]
            current_moment["context_found_filtered"] = max(current_moment["context_found"], key=lambda x: x["relevant_percentage"]) if len(current_moment["context_found"]) > 0 else {}
            
        return moment_result

    def check_transcription(self, moment_result, transcript):

        for moment in moment_result:
            print("moment: ", moment["moment"])
            if len(moment["categories_found"]) == 0:
                continue
            fragment_start = self.normalize(moment["categories_found"][0]['fragment_found'])
            fragment_end = self.normalize(moment["categories_found"][-1]['fragment_found'])
            print("fragment_start: ", fragment_start)
            print("fragment_end: ", fragment_end)
            indexes_start = [match.start() for match in re.finditer(fragment_start, transcript)]
            indexes_end = [match.end() for match in re.finditer(fragment_end, transcript)]
            print("indexes_start: ", indexes_start)
            print("indexes_end: ", indexes_end)
            fragment_index_start = indexes_start[0]
            fragment_index_end = indexes_end[0]
            print("fragment_index_start: ", fragment_index_start)
            print("fragment_index_end: ", fragment_index_end)
            if moment["order"] == 1:
                fragment_index_start = 0
            if moment["order"] == len(moment_result):
                fragment_index_start = len(transcript)-1
            moment["transcript_found"] = transcript[fragment_index_start:fragment_index_end]
            print("transcript_found: ", moment["transcript_found"])
        
        return moment_result

    def qualify(self, moment_result):
        for moment in moment_result:
            categories = [
                    f"{e['category']}-{e['subcategory']}" for e in moment['categories_found']
                    if e["id"] in moment["context_found_filtered"]["context"]
                ]

            if moment['mode'] == 'ALL':
                moment["if_found"] = all(element in categories for element in moment['categories'])
                # moment["if_found"] = all(element in moment['categories_found'] for element in moment['categories'])
            else:
                moment["if_found"] = any(element in categories for element in moment['categories'])
                # moment["if_found"] = any(element in moment['categories_found'] for element in moment['categories'])
        
        return moment_result
    
    def result_data(self, moment_result):
        moment_final_result = []
        for moment in moment_result:
            categories_found_context = [
                    f"{e['category']}-{e['subcategory']}" for e in moment['categories_found']
                    if e["id"] in moment["context_found_filtered"]["context"]
                ]
            unique_list_categories = []
        
            for category in categories_found_context:
                if category not in unique_list_categories:
                    unique_list_categories.append(category)

            moment_final_result.append({
                "order": moment["order"],
                "moment": moment["moment"],
                "mode": moment["mode"],
                "if_found": moment["if_found"],
                "original_categories": moment["categories"],
                "categories_found": unique_list_categories,
                "credibility_percentage": moment["context_found_filtered"]["relevant_percentage"] if len(moment["context_found_filtered"]) > 0 else 0,
                "transcript_found": moment["transcript_found"]
            })
        
        return moment_final_result
        
    def main(self):
        try:
            self.get_data()

            result_map = self.map_moments(self.moments, self.categories_found)
            result_context = self.check_context(result_map, value_mode_context=3)
            result_moments = self.check_moments(result_context, self.moments, self.categories_found, value_mode_moment=3)
            result_transcription = self.check_transcription(result_moments, self.transcript)
            result_qualify = self.qualify(result_transcription)
            result_data = self.result_data(result_qualify)

            self.write_data(result_data, "result.json")
            self.write_data({"text": self.transcript}, "transcript_normalize.json")
            print("---SUCCESS---")
        except Exception as e:
            print("FAIL")
            print(e)

Moments()