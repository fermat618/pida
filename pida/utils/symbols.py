

class Symbols(object):

    def __init__(self, name, items):
        self.items = {}
        self.name = name
        for index, value in enumerate(items):
            if not value.islower():
                raise ValueError('%s is not lower')
            self.items[index] = value
            self.items[value] = index
            setattr(self, value.upper(), value)

    def key(self, item):
        """
        :param str item: one of the symbols

        key function for sorting a list of symbols
        everything str thats not in this symbol bag gets sorted last
        """
        return self.items.get(item.lower(), len(self.items))

    def __contains__(self, key):
        return key.lower() in self.items

    def __getitem__(self, item):
        return self.items[item]

    def __iter__(self):
        raise TypeError("a bag of symbols is not iterable")
