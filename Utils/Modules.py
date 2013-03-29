from importlib import import_module
from imp import reload
from sys import modules

class Modules:

    def __init__(self):
        self.modules = {}
    
    def getModule(self, moduleName):
        """
            Searches for module in loaded modules and returns it if it's found.
        """
        
        if moduleName in self.modules:
            tmp = moduleName
            if moduleName.find(".") != -1:
                tmp = moduleName.split(".", 1)[1]
            return getattr(modules[moduleName], tmp)
        
        else: return None
    
    def getModules(self):
        """
            Returns the dict storing all the loaded modules.
        """
        
        return self.modules
        
    def loadModule(self, moduleName):
        """
            Attempts to load a module from IRCCommand subfolder and stores the module in a dict
            if it's successful.
        """
        
        if moduleName in self.modules:
            return False
        
        try:
            module = import_module(moduleName)
            self.modules[moduleName] = module
            return True
        
        except ImportError:
            return False
    
    def reloadModule(self, moduleName):
        """
            Attempts to reload a module by passing the old import object to imp.reload() which
            returns the new import object if reload was successful.
        """
        
        if moduleName in self.modules:
            self.modules[moduleName] = reload(self.modules[moduleName])
            return True
                
        else:
            return False
            