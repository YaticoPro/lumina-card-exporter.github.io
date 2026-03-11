import os
import re
import csv
import pickle

class Cost:
    """
    Class representing the cost of a card
    """
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
    """
    Class representing a card
    """
    id, title, card_type, cost, identity, swiftness, effect, version, extension, attack, defense, nation, card_class = [None]*13
    def __init__(self, header, row, mapping, mapping_transformer=None):
        if mapping_transformer is None:
            mapping_transformer = {}
        for k, v in zip(header, row):
            if k in mapping:
                k = mapping[k]
                if k in mapping_transformer:
                    v = mapping_transformer[k](v)
                setattr(self, k, v)

def string_to_cost(cost_string) -> Cost:
    """
    From 2E + 1T + 2
    To a Cost instance
    """
    regex_cost = re.compile("([0-9]+)([A-Z])*")
    match = regex_cost.findall(cost_string)
    cost_dict = {y:int(x) for x,y in match}
    return Cost(cost_dict)

def identity_splitter(x) -> list[str]:
    """
    From a string of words separated by a comma and space
    To a list of words, add `Neutre` if no word found
    """
    identities = x.split(", ")
    identities = [identity for identity in identities if identity]
    if not len(identities):
        return ["Neutre"]
    return identities

class CardImporter:
    """
    Class transforming the csv file into a list of Card instances and
    importing the Cards into a pickle format
    """
    pickle_path = "./cards/"
    mapping = {'ID': 'id','Nom': 'title', 'Type': 'card_type', 'Coût':'cost', 'Identité': 'identity', 'Vitesse': 'swiftness',
               'Effet':'effect', 'Peuple':'nation', 'Classe':'card_class', 'ATK':'attack', 'DEF':'defense',
               'Version':'version', 'Extension':'extension'}
    option_int = lambda x: int(x) if x.isdigit() else None
    mapping_transformer = {'attack': option_int, 'defense': option_int, 'cost':string_to_cost, 'identity': identity_splitter}

    def parse(self, csv_file, mapping=None, limit=None):
        if mapping is None:
            mapping = self.mapping
        with open(csv_file, "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            header = csv_reader.__next__()
            i = 0
            ids = set()
            for row in csv_reader:
                new_card = Card(header, row, mapping, self.mapping_transformer)
                if not new_card.id and new_card.title:
                    print(f"Card id not found for {new_card.title}, generating new id")
                    new_card.id = new_card.title.replace(" ", "_")
                ids.add(new_card.id)
                if id in ids:
                    print(f"Card id in conflict {new_card.id}")
                with open(f"{self.pickle_path}{new_card.id}.pickle", "wb") as pickle_file:
                    pickle.dump(new_card, pickle_file)
                i += 1


                if limit is not None and i > limit:
                    break

    def delete_pickles(self):
        for file in os.listdir(f"{self.pickle_path}"):
            if file.endswith(".pickle"):
                os.remove(f"{self.pickle_path}{file}")