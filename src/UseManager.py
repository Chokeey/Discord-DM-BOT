class UseManager:
    # Given a map, will flag which key value is in use outside the manager.
    def __init__(self, hashmap):
        self.hashmap = hashmap
        self.inUse = []

    def useValue(self):
        for key in self.hashmap:
            if key not in self.inUse:
                self.setValueInUse(key)
                return key

    def isInUse(self, key):
        return key in self.inUse

    def setValueInUse(self, val):
        if val not in self.inUse:
            self.inUse.append(val)

    def freeValue(self, val):
        if val in self.inUse:
            self.inUse.remove(val)

    def get(self):
        return self.hashmap
