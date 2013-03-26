from queue import Queue
from time import sleep
from threading import Thread
import sys

class IRCCommand:

    def __init__(self, commandOutputQueue, logging):
        self.logging = logging
        self.taskManager = TaskManager(commandOutputQueue)
        self.modules = []
    
    def loadModule(self, moduleName):
        try:
            __import__("IRCCommand." + moduleName, fromlist=[moduleName])
            self.modules.append(moduleName)
            return True
        
        except ImportError:
            return False
    
    
    def dispatchCommand(self, server, channel, sender, login, hostname, message, type):
        """
            Checks whether the message contains a valid command and then sends a Command object
            to the inputCommandHandler.
        """
        tmp = message.split(" ", 1)
        
        if len(tmp) > 1:
            command = Command(server, channel, sender, tmp[0].strip(), tmp[1].strip(), type)
        
        else:
            command = Command(server, channel, sender, tmp[0].strip(), "", type)
        
        for module in self.modules:
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
    
    def __init__(self, server, channel, sender, command, message, type, privilege = "normal"):
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
                self.commandOutputQueue.put(task[0](task[1]))
                
            else:
                sleep(0.5)
                