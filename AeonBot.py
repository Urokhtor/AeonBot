from AeonBot.IRCinterface import IRCinterface
from AeonBot.EventHandler import EventHandler
from AeonBot.EventDispatcher import EventDispatcher
from AeonBot.Event import Event
from AeonBot.Logging import Logging
from AeonBot.ReplyConstants import *
from queue import Queue
from threading import Thread
from time import sleep

class AeonBot(Thread, EventHandler):
    """
        The heart of this IRC API
    """
    
    def __init__(self):
        Thread.__init__(self)
        
        self.running = True
        self.nickInUseSuffix = "_"
        
        self.inputQueue = Queue()
        self.logging = Logging()
        self.irc = IRCinterface(self.inputQueue, self.logging, self.running)
        self.eventDispatcher = EventDispatcher(self, self.logging, self.running)
        EventHandler.__init__(self, self.irc, self.logging)
        
        self.start()
    
    def setNickInUseSuffix(self, suffix):
        """
            Sets the nicksuffix that is used by default when onNickInUse() event is called.
        """
        
        self.nickInUseSuffix = suffix
    
    def getNickInUseSuffix(self):
        """
            Returns the nicksuffix.
        """
        
        return self.nickInUseSuffix
        
    def processServerResponse(self, server, code, target, response):
        """
            Processes some important server responses that can be found from ReplyConstants.py.
            Every response hit MUST return True to let the message handler know whether it should
            dispatch the message in EventDispatcher, or discard it.
        """
        
        returnFlag = False
        
        if code == RPL_NAMREPLY:
            if response.startswith("=") or response.startswith("@") or response.startswith("*"):
                users = response.split(":")[1].split()
                channel = response.split()[1]
                tmp = ""
                
                # Check that we're actually on the channel and then add the users to the channel userlist.
                if self.irc.ConnectionManager[server].getChannelManager().findChannel(channel):
                    for user in users:
                        if self.irc.ConnectionManager[server].getChannelManager().getChannel(channel).addUser(user):
                            tmp += user + " "
                            
                if not tmp.strip() == "": self.logging.debug(server, "Added user(s) " + tmp.strip() + " to channel list.")
                
            returnFlag = True
    
        # Handle nick already in use error.
        elif code == ERR_NICKNAMEINUSE:
            self.onNickInUse(server)
            returnFlag = True
        
        # If we find this reply constant from a line, we know we are successfully connected
        # to a server, therefore we can initiate onConnect event which lets user to handle
        # routines that happen when a server is ready for commands, like joinin channels.
        elif code == RPL_ENDOFMOTD:
            self.onConnect(server)
            returnFlag = True
        
        self.onServerResponse(server, code, response)
        return returnFlag
            
    def run(self):
        """
            This thread handles the message parsing and dispatching. It polls the inputqueue that is dedicated
            to all the server connections and then sniffs for certain events that should be handled as soon as
            possible (i.e. PING). It also parses the incoming message and produces an event dump that is sent
            to the EventDispatcher for further processing.
        """
        
        try:
            while self.running:
                try:
                    if not self.inputQueue.empty():
                        line = self.inputQueue.get()
                        tmp = line.split() # Keep original line untouched and use tmp for various bits of information needed
                        
                        #Handle PING requests, needed to keep bot connected to a server.
                        if tmp[1] == "PING":
                            self.onServerPing(tmp[0], tmp[2])
                            continue
                        
                        # All the needed info about the received line will be parsed to these variables
                        # for further handling.
                        name = ""
                        login = ""
                        hostname = ""
                        target = ""
                        message = ""
                        server = tmp[0]
                        senderInfo = tmp[1]
                        type = tmp[2]
                        
                        # Just some info received when you open a server connection.
                        if senderInfo == "NOTICE": continue
                        
                        else:
                            if senderInfo.find("!") != -1 and senderInfo.find("@") != -1:
                                name = tmp[1].split("!")[0][1:]
                                login = tmp[1].split("!")[1].split("@")[0]
                                hostname = tmp[1].split("!")[1].split("@")[1]
                                target = tmp[3]
                            
                            else:
                                hostname = tmp[1][1:]
                                target = tmp[3]
                            
                            # If line contains a message and it's not a response to some of our actions, i.e.
                            # JOIN for example (server returns a JOIN command without message when you send
                            # a join request to it).
                            if len(tmp) > 4:
                                if name != self.irc.ConnectionManager[server].getNick() and tmp[4].startswith(":"): message = line.split(":")[2]
                                else: message = line.split(" ", 4)[4]

                        if self.processServerResponse(server, type, target, message): continue
                        
                        self.eventDispatcher.eventQueue.put(Event(server, type, target, name, login, hostname, message, line))
                        continue # If we handled a line, check if queue has waiting messages.
                    sleep(0.2) # If queue was empty, wait a bit and check again.
                
                except Exception as e:
                    self.logging.error("Core message:", "Encountered an error while parsing incoming server traffic: '" + line + "', reason: " + str(e))
        finally:
            self.logging.error("Core message:", "Message handler crashed.")
    