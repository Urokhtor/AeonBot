from queue import Queue
from time import sleep
from threading import Thread
from threading import Lock
from sys import modules
from random import randint

class IRCCommand:

    def __init__(self, bot):
        self.bot = bot
        self.taskManager = TaskManager(self.bot.commandOutputQueue)

    def dispatchCommand(self, server, channel, sender, login, hostname, message, type):
        """
            Creates a command object and goes through loaded modules. If we find a match for the
            wanted command we get the function and dispatch it to the task manager which handles
            executing it correspondingly.
        """
        tmp = message.split(" ", 1)
        host = "*!" + login + "@" + hostname # To make Utils.Decorators happy.
        
        if len(tmp) > 1: command = Command(self.bot, server, channel, sender, host, tmp[0].strip(), tmp[1].strip(), type)
        else: command = Command(self.bot, server, channel, sender, host, tmp[0].strip(), "", type)
        
        for func in self.bot.registeredFunctions:
            self.bot.messageInputQueue.put((func, command))
            
        for module, moduleObject in self.bot.subsystems["modules"].getModules().items():
            className = ""
            
            if module.find(".") != -1: className = module.split(".", 1)[1]
                
            try: self.taskManager.addTask((getattr(getattr(modules[module], className), tmp[0]), command))
            except AttributeError: pass

        
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
    
    def __init__(self, bot, server, channel, sender, host, command, message, type):
        self.bot = bot # Bot object so commands can access its functions
        self.server = server # Server where the request originated from
        self.channel = channel # Channel where the request originated from
        self.sender = sender # User who triggered the command
        self.host = host # User's host
        self.command = command # Name of the command
        self.message = message # The message part
        self.type = type # Accepted types: message, query, action, raw. Defines what kind of message the request was
        self.result = "" # Store the resulting string here, it will be returned to IRC as the result of the command.
        
class TaskManager:
    """
        The purpose of this task manager is to allow adding routines that need to be executed and then
        executing them in the worker threads.
        
        Thanks for i7c's mibs dispatcher for guidelines about how this should work.
    """
    
    def __init__(self, commandOutputQueue, threadCount = 2):
        self.commandOutputQueue = commandOutputQueue
        self.threadCount = threadCount # Current worker thread count.
        self.targetCount = threadCount # How many worker threads we want to maintain.
        self.workers = {}
        self.tasks = Queue()
        self.busyThreads = 0 # Number of threads executing a task.
        
        # Initialize the wanted number of workers.
        for i in range(0, self.targetCount):
            workerThread = Thread(target = self.executeTasks, name = str(i+1)).start()
            self.workers[str(i+1)] = workerThread
            
    def addTask(self, taskTuple):
        """
            Adds the task in task manager's internal taks queue and adds new worker
            threads if all the current ones are busy executing tasks.
        """
        
        self.tasks.put(taskTuple)
        
        # Spawn a new worker thread if all the current ones are busy executing a task.
        if self.tasks.qsize() > 0 and self.threadCount <= self.busyThreads:
            lock = Lock()
            lock.acquire()
            self.threadCount += 1
            threadName = str(randint(0, 9999))
            workerThread = Thread(target = self.executeTasks, name = threadName).start()
            self.workers[threadName] = workerThread
            lock.release()

    def executeTasks(self):
        """
            Polls internal taks queue for tasks and if finds one, tries to execute it.
            Also handles removing free worker threads if there are more than the wanted
            number.
        """
        
        lock = Lock()
        
        while True:
            if not self.tasks.empty():
                task = self.tasks.get()
                
                # Execute the function and put its return value in bot's queue which is used to
                # handle outgoing traffic. It looks bit stupid because of that lock, but it's important
                # to keep your threaded code safe!
                lock.acquire()
                self.busyThreads += 1
                lock.release()
                try: self.commandOutputQueue.put(task[0](task[1]))
                except: pass
                lock.acquire()
                self.busyThreads -= 1
                lock.release()
                
            else:
                # If task queue is empty and there are at least two more threads than those that are busy
                # (for example 2 threads are busy running a long task and 2 threads are free to hanle incoming
                # tasks but we only want to run 2 threads, then destroy one of the free threads), check if any
                # other threads are dead and end the current thread.
                if self.tasks.qsize() == 0 and self.threadCount > self.targetCount and self.threadCount > self.busyThreads + 1:
                    lock.acquire()
                    
                    for name, thread in self.workers.items():
                        if thread == None:
                            del self.workers[name]
                            self.threadCount -= 1
                            break
                            
                    lock.release()    
                    return
                        
                sleep(0.2)
                