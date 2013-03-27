from queue import Queue
from time import sleep
from threading import Thread
from imp import reload
import sys

class IRCCommand:

    def __init__(self, bot):
        self.bot = bot
        self.taskManager = TaskManager(self.bot.commandOutputQueue)
        self.modules = {}
    
    def loadModule(self, moduleName):
        """
            Attempts to load a module from IRCCommand subfolder and stores the module in a dict
            if it's successful.
        """
        
        if moduleName in self.modules:
            return False
            
        try:
            module = __import__("IRCCommand." + moduleName, fromlist=[moduleName])
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
    
    def dispatchCommand(self, server, channel, sender, login, hostname, message, type):
        """
            Creates a command object and goes through loaded modules. If we find a match for the
            wanted command we get the function and dispatch it to the task manager which handles
            executing it correspondingly.
        """
        tmp = message.split(" ", 1)
        
        if len(tmp) > 1:
            command = Command(self.bot, server, channel, sender, tmp[0].strip(), tmp[1].strip(), type)
        
        else:
            command = Command(self.bot, server, channel, sender, tmp[0].strip(), "", type)
        
        for module, moduleObject in self.modules.items():
            try:
                self.taskManager.addTask((getattr(getattr(sys.modules["IRCCommand." + module], module), tmp[0]), command))
            except AttributeError:
                pass
    
class Command:
    """
        This utility is used to compose the command object which unifies the handling of command messages.
        Fields server and channel mark the source of the command. Command itself is the command that is
        requested. Message is the message information for the command, if needed. Type denotes the type of
        action that the bot should perform when responding to the command. This type is set by the command
        handler, not by the user. Also the original command message is replaced by the command response by the
        command handler. Channel might be changed by the command handler if the type of the command is something
        like "speak [channel] [message]".
    """
    
    def __init__(self, bot, server, channel, sender, command, message, type, privilege = "normal"):
        self.bot = bot # Bot object so commands can access its functions
        self.server = server # Server where the request originated from
        self.channel = channel # Channel where the request originated from
        self.sender = sender # User who triggered the command
        self.command = command # Name of the command
        self.message = message # The message part
        self.type = type # Accepted types: message, query, action, raw. Defines what kind of message the request was
        self.privilege = privilege # Accepts types: normal, master, owner
        self.result = "" # Store the resulting string here, it will be returned to IRC as the result of the command.
        
class TaskManager:
    """
        The purpose of this task manager is to allow adding routines that need to be executed and then
        executing them in the worker threads.
        
        Thanks for i7c's mibs dispatcher for guidelines about how this should work.
    """
    
    def __init__(self, commandOutputQueue, threadCount = 2):
        self.commandOutputQueue = commandOutputQueue
        self.threadCount = threadCount
        self.workers = []
        self.tasks = Queue()
        
        for i in range(0, self.threadCount):
            workerThread = Thread(target = self.executeTasks).start()
            self.workers.append(workerThread)
            
    def addTask(self, taskTuple):
        self.tasks.put(taskTuple)

    def executeTasks(self):
        while True:
            if not self.tasks.empty():
                task = self.tasks.get()
                
                # Execute the function and put its return value in bot's queue which is used to
                # handle outgoing traffic.
                try: self.commandOutputQueue.put(task[0](task[1]))
                except: pass
                
            else:
                sleep(0.5)
                