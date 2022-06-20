from json import JSONEncoder


class ObjectDict(JSONEncoder):
    def default(self, o):
        try:
            return o.__dict__
        except AttributeError:
            return {}
