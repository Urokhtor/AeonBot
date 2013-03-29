import json

class Config:

    def __init__(self, confFile):
        f = open(confFile, "r")
        self.data = json.load(f)
        f.close()
        self.confFile = confFile

    def _write(self):
        f = open(self.confFile, "w")
        json.dump(self.data, f, indent = 4)
        f.close()
    
    def setItem(self, key, value):
        self.data[key] = value
        self._write()
    
    def getItem(self, key, default):
        return self.data.get(key, default)
        
    def items(self):
        return self.data.items()