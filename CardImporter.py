import os
import re
import csv
import pickle

class Cost:
    E,F,G,O,N,T,neutral=0,0,0,0,0,0,0
    def __init__(self, dictionary):
        for k, v in dictionary.items():
            if k == "":
                self.neutral = v
            elif k in dir(self):
                setattr(self, k, v)
            else:
                raise Exception(f"Unknown element : {k}")

    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith("__") and self.__getattribute__(attr) != 0:
                yield attr, getattr(self, attr)

class Card:
    def __init__(self, header, row, mapping, mapping_transformer=None):
        if mapping_transformer is None:
            mapping_transformer = {}
        for k, v in zip(header, row):
            if k in mapping:
                k = mapping[k]
                if k in mapping_transformer:
                    v = mapping_transformer[k](v)
                setattr(self, k, v)

def string_to_cost(cost_string):
    regex_cost = re.compile("([0-9]+)([A-Z])*")
    match = regex_cost.findall(cost_string)
    cost_dict = {y:int(x) for x,y in match}
    return Cost(cost_dict)

def identity_splitter(x):
    identities = x.split(", ")
    identities = [identity for identity in identities if identity]
    if not len(identities):
        return ["Neutre"]
    return identities

class CardImporter:
    pickle_path = "./cards/"
    mapping = {'ID': 'id','Nom': 'title', 'Type': 'card_type', 'Coût':'cost', 'Identité': 'identity', 'Vitesse': 'swiftness',
               'Effet':'effect', 'Peuple':'nation', 'Classe':'card_class', 'ATK':'attack', 'DEF':'defense',
               'Version':'version', 'Extension':'extension'}
    option_int = lambda x: int(x) if x.isdigit() else None
    mapping_transformer = {'attack': option_int, 'defense': option_int, 'cost':string_to_cost, 'identity': identity_splitter}

    def parse(self, csv_file, mapping=None, limit=None):
        if mapping is None:
            mapping = self.mapping
        with open(csv_file, "r") as f:
            csv_reader = csv.reader(f, delimiter=",")
            header = csv_reader.__next__()
            i = 0
            for row in csv_reader:
                new_card = Card(header, row, mapping, self.mapping_transformer)
                if new_card.id:
                    with open(f"{self.pickle_path}{new_card.id}.pickle", "wb") as f:
                        pickle.dump(new_card, f)
                    i += 1
                if limit is not None and i > limit:
                    break

    def delete_pickles(self):
        for file in os.listdir(f"{self.pickle_path}"):
            if file.endswith(".pickle"):
                os.remove(f"{self.pickle_path}{file}")

if __name__ == '__main__':
    ci = CardImporter()
    ci.parse("./files/lumina_0_1.csv")