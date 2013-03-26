from AeonBot.Event import Event
from AeonBot.ReplyConstants import *
from queue import Queue
from threading import Thread
from time import sleep

class EventDispatcher(Thread):
    """
        Uses an event queue to read events sent to the bot. It then further processes the event type
        and calls the appropriate event method from EventHandler.
    """
    
    def __init__(self, parent, logging, running):
        Thread.__init__(self)
        self.parent = parent
        self.running = running
        self.logging = logging
        self.eventQueue = Queue()
        self.channelPrefix = ["#", "!", "&", "+"]
        self.start()

    
    def processMode(self, server, channel, nick, login, hostname, mode):
        """
            This method processes the mode event mainly because we need to keep the channel nicklist
            in sync (voices, ops, devoices, deops), once this is handled EventHandler's onMode() method
            is called which is handled by the user.
        """
        
        # Check if any usermodes are changed, if so read through the message to see whose flags have been
        # changed and update it to the channelmanager.
        if mode.split()[0].find("o") != -1 or mode.split()[0].find("v") != -1:
            modes = mode.split()[0]
            users = mode.split(" ", 1)[1]
            seeking = ""
            i = 0
            
            for c in modes:
                # The mode messages should be grouped so that taking some flag away happens first, then
                # comes adding flags. Seeking is used to keep track of what we are doing with the flags,
                # i.e. are we opping or deopping.
                if c == "-":
                    seeking = "-"
                    continue
                    
                elif c == "+":
                    seeking = "+"
                    continue
                
                # If we found an op flag event, first check to see that the user in question exist, if so then
                # proceed to either op/voice or deop/devoice the user according to the seeking flag.
                elif c == "o":
                    userFound = self.parent.irc.ConnectionManager[server].getChannelManager().getChannel(channel).findUser(users.split()[i])
                    if not userFound: continue
                        
                    if seeking == "-": self.parent.irc.ConnectionManager[server].getChannelManager().getChannel(channel).getUser(users.split()[i]).removeOp()
                    elif seeking == "+": self.parent.irc.ConnectionManager[server].getChannelManager().getChannel(channel).getUser(users.split()[i]).addOp()
                
                elif c == "v":
                    userFound = self.parent.irc.ConnectionManager[server].getChannelManager().getChannel(channel).findUser(users.split()[i])
                    if not userFound: continue
                    
                    if seeking == "-": self.parent.irc.ConnectionManager[server].getChannelManager().getChannel(channel).getUser(users.split()[i]).removeVoice()
                    elif seeking == "+": self.parent.irc.ConnectionManager[server].getChannelManager().getChannel(channel).getUser(users.split()[i]).addVoice()
                
                # Increment the counter. It is used to keep track of how manynth user we need to process, because
                # the mode messages are of form: -vo+o user1 user2 user3. So variable i is used to track which
                # user we're currently modifying.
                i += 1
                
        self.parent.onMode(server, channel, nick, login, hostname, mode)
        
    def run(self):
        """
            The actual dispatcher. It compares the event type to different kinds of IRC events and then
            calls the correct function in the bot's EventHandler.
        """
        
        while self.running:
            try:
                # Read the event object from event queue.
                event = self.eventQueue.get()
                
                # Handle CTCP requests directed at us.
                if event.type == "PRIVMSG" and event.message.startswith("\001") and event.message.endswith("\001"):
                    if event.message.find("ACTION") != -1: self.parent.onAction(event.server, event.target, event.name, event.login, event.hostname, event.message.split(" ", 1)[1].split("\001")[0])
                    elif event.message.find("VERSION") != -1: self.parent.onVersion(event.server, event.name, event.login, event.hostname, event.target)
                    elif event.message.find("PING") != -1: self.parent.onPing(event.server, event.name, event.login, event.hostname, event.target, event.message.split()[1].split("\001")[0])
                    elif event.message.find("TIME") != -1: self.parent.onTime(event.server, event.name, event.login, event.hostname, event.target)
                    elif event.message.find("FINGER") != -1: self.parent.onFinger(event.server, event.name, event.login, event.hostname, event.target)
                    else: self.parent.onUnknown(event.line)
                            
                elif event.type == "PRIVMSG" and self.channelPrefix.count(event.target[:1]) > 0:
                    try: self.parent.onMessage(event.server, event.target, event.name, event.login, event.hostname, event.message)
                    except Exception as e: self.logging.error(event.server, "Error: Method onMessage encountered an error: " + str(e))
                        
                elif event.type == "PRIVMSG":
                    try: self.parent.onPrivateMessage(event.server, event.name, event.login, event.hostname, event.message)
                    except Exception as e: self.logging.error(event.server, "Error: Method onPrivateMessage encountered an error: " + str(e))
                            
                elif event.type == "JOIN":
                    try:
                        if event.name != self.parent.irc.ConnectionManager[event.server].getNick():
                            if self.parent.irc.ConnectionManager[event.server].getChannelManager().findChannel(event.target):
                                if self.parent.irc.ConnectionManager[event.server].getChannelManager().getChannel(event.target).addUser(event.name):
                                    self.logging.debug(event.server, "Added user " + event.name + " to channel " + event.target + " list")
                                    
                        self.parent.onJoin(event.server, event.target, event.name, event.login, event.hostname)
                    
                    except Exception as e:
                        self.logging.error(event.server, "Error: Method onJoin encountered an error: " + str(e))
                            
                elif event.type == "PART":
                    try:
                        if event.name != self.parent.irc.ConnectionManager[event.server].getNick():
                            if self.parent.irc.ConnectionManager[event.server].getChannelManager().findChannel(event.target):
                                if self.parent.irc.ConnectionManager[event.server].getChannelManager().getChannel(event.target).removeUser(event.name):
                                    self.logging.debug(event.server, "Removed user " + event.name + " from channel " + event.target + " list")
                                    
                        self.parent.onPart(event.server, event.target, event.name, event.login, event.hostname)
                    
                    except Exception as e:
                        self.logging.error(event.server, "Error: Method onPart encountered an error: " + str(e))
                            
                elif event.type == "NICK":
                    try: self.parent.onNick(event.server, event.name, event.login, event.hostname, event.target)
                    except Exception as e: self.logging.error(event.server, "Error: Method onNick encountered and error: " + str(e))
                            
                elif event.type == "NOTICE":
                    try: self.parent.onNotice(event.server, event.target, event.name, event.login, event.hostname, event.message)
                    except Exception as e: self.logging.error(event.server, "Error: Method onNotice encountered an error: " + str(e))
                            
                elif event.type == "QUIT":
                    try: self.parent.onQuit(event.server, event.name, event.login, event.hostname, event.message)
                    except Exception as e: self.logging.error(event.server, "Error: Method onQuit encountered an error: " + str(e))
                            
                elif event.type == "KICK":
                    try:
                        # Remove the channel from the list if we are kicked out. I know, terribly handled,
                        # but can't really be done anywhere else logically.
                        if event.message.split()[0] == self.parent.irc.ConnectionManager[event.server].getNick():
                            self.logging.debug(event.server, "We were kicked from channel " + event.target + " by " + event.name)
                            
                            if self.parent.irc.ConnectionManager[event.server].getChannelManager().findChannel(event.target):
                                self.parent.irc.ConnectionManager[event.server].getChannelManager().removeChannel(event.target)
                        
                        else:
                            if self.parent.irc.ConnectionManager[event.server].getChannelManager().findChannel(event.target):
                                self.parent.irc.ConnectionManager[event.server].getChannelManager().getChannel(event.target).removeUser(event.message.split()[0])
                                self.logging.debug(event.server, "User " + event.message.split()[0] + " was kicked from channel " + event.target)
                        
                        self.parent.onKick(event.server, event.target, event.name, event.login, event.hostname, event.message.split()[0], event.message.split(":")[1])
                    
                    except Exception as e:
                        self.logging.error(event.server, "Error: Method onKick encountered an error: " + str(e))
                            
                elif event.type == "MODE":
                    try: self.processMode(event.server, event.target, event.name, event.login, event.hostname, event.message)
                    except Exception as e: self.logging.error(event.server, "Error: Method onMode encountered an error: " + str(e))
                            
                elif event.type == "TOPIC":
                    try: self.parent.onTopic(event.server, event.target, event.name, event.login, event.hostname, event.message)
                    except Exception as e: self.logging.error(event.server, "Error: Method onTopic encountered an error: " + str(e))
                            
                elif event.type == "INVITE":
                    try: self.parent.onInvite(event.server, event.message, event.name, event.login, event.hostname)
                    except: self.logging.error(event.server, "Error: Method onInvite encountered an error: " + str(e))
                
                elif event.type == "DISCONNECTION":
                    try: self.parent.onDisconnect(event.server)
                    except Exception as e: self.logging.error(event.server, "Error: Method onDisconnect encountered an error: " + str(e))
                            
                else:
                    self.parent.onUnknown(event.line)
                        
                sleep(0.05)
                
            except Exception as e:
                self.logging.error(event.server, "Event dispatcher encountered an error while handling an event: " + e)