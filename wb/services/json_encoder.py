from json import JSONEncoder


class ObjectDict(JSONEncoder):
    def default(self, o):
        return o.__dict__
