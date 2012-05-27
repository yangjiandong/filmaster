class ListWrapper(object):
    def __init__(self, list):
        self.list = list

    def __getitem__(self, i):
        if isinstance(i, slice):
            self.list = self.list[i]
            return self
        if isinstance(i, (int, long)):
            return iter(self.wrap( (self.list[i], ) )).next()

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.wrap(self.list))

    def wrap(self, items):
        raise NotImplementedError()

