from json import JSONEncoder


class Directory:
    def __init__(self, data: dict | list):
        self._data = data

    def __iter__(self):
        if type(self._data) == list:
            return iter(enumerate(self._data))
        elif type(self._data) == dict:
            return iter(self._data.items())

    def __str__(self):
        return '\n'.join([str(k) + '/'
                         if isinstance(v, Directory)
                         else str(k)
                         for k, v in self])

    def recurse(self):
        for k, v in self:
            if type(v) in [list, dict]:
                v = Directory(v)
            if isinstance(v, Directory):
                for line in v.recurse():
                    yield f'{k}/{line}'
            elif v:
                yield f'{k} {v}'

    def get(self, key: str):
        if type(self._data) == list:
            if len(self._data) == 1 and key != '0':
                if isinstance(member := self._data[0], Directory):
                    return member.get(key)
                else:
                    raise NotDir(f'{member} is not a directory')
            return self._data[int(key)]
        elif type(self._data) == dict:
            return self._data.get(key)

    def data(self):
        return self._data


class NotDir(KeyError):
    """Raised when trying to access a value from a key that isn't a directory"""
    pass


class TrailingSlash(Exception):
    """Raised when key that is not a directory is referenced as if it was (ie /project-id/ )"""
    pass


class MissingSlash(Exception):
    """Raised when key that is dictionary is referenced as if it were a simple value (ie /attributes )"""
    pass


class CustomEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Directory):
            return o.data()
